# indexer_searcher/indexer.py

import json
import os
import math
import struct
from pathlib import Path
from bs4 import BeautifulSoup
from tokenizer import get_token_frequencies
from InvertedIndex import FrequencyList
from typing import Dict, List, Tuple

"""
MusicMatcher Indexer

Builds an inverted index from crawled product HTML stored in crawled_data/.

Input:
    crawled_data/<domain>/*.json
    Each JSON file should contain:
        - "url": str
        - "content": str (raw HTML)
        - "product": {...} (optional metadata)

Output:
    - postings.bin  (binary postings)
    - vocab.json    (token -> offset/length)
    - doc_map.json  (doc_id -> {url, total_tokens, product})
"""

# ----------------------- Config ----------------------
CRAWLED_FOLDER = Path("crawled_data")

VOCAB_FINAL = Path("vocab.json")
DOCMAP_FINAL = Path("doc_map.json")
POSTINGS_FINAL = Path("postings.bin")

SEG_VOCAB = "vocab_seg_{i}.json"
SEG_POSTINGS = "postings_seg_{i}.bin"
SEG_DOCMAP = "doc_map_seg_{i}.json"

MIN_SEGMENTS = 3


# ----------------------- VarByte Encoding Helpers ----------------------
def vb_encode_number(n: int) -> bytes:
    tmp = []
    while True:
        tmp.insert(0, n % 128)
        if n < 128:
            break
        n //= 128
    tmp[-1] += 128
    return bytes(bytearray(tmp))


def vb_encode_list(nums: List[int]) -> bytes:
    out = bytearray()
    for n in nums:
        out.extend(vb_encode_number(n))
    return bytes(out)


# ----------------------- Segment Writer Utility ----------------------
def write_segment_postings_and_vocab(
    postings: Dict[str, List[Tuple[int, float]]],
    out_postings_path: Path,
    out_vocab_path: Path
):
    offset = 0
    vocab = {}
    with open(out_postings_path, "wb") as pf:
        for token in sorted(postings.keys()):
            plist = postings[token]
            plist.sort(key=lambda x: x[0])

            token_bytes = bytearray()
            prev = 0
            for doc_id, tf in plist:
                delta = doc_id - prev
                token_bytes.extend(vb_encode_number(delta))
                token_bytes.extend(struct.pack("<f", float(tf)))
                prev = doc_id

            pf.write(token_bytes)
            vocab[token] = {"offset": offset, "length": len(token_bytes)}
            offset += len(token_bytes)

    with open(out_vocab_path, "w", encoding="utf-8") as vf:
        json.dump(vocab, vf, indent=2)


# ----------------------- Segment Reader Utility ----------------------
def read_segment_postings(seg_postings_path: Path, seg_vocab: Dict[str, Dict]) -> Dict[str, List[Tuple[int, float]]]:
    out = {}
    with open(seg_postings_path, "rb") as pf:
        for token, meta in seg_vocab.items():
            offset = meta["offset"]
            length = meta["length"]
            pf.seek(offset)
            raw = pf.read(length)
            i = 0
            doc_id = 0
            lst = []
            while i < len(raw):
                val = 0
                while True:
                    byte = raw[i]
                    i += 1
                    if byte >= 128:
                        val = (val << 7) | (byte - 128)
                        break
                    else:
                        val = (val << 7) | byte
                delta = val
                doc_id += delta
                tf = struct.unpack("<f", raw[i:i+4])[0]
                i += 4
                lst.append((doc_id, tf))
            out[token] = lst
    return out


# ----------------------- Main Indexer Flow ----------------------
def build_index():
    """
    1. Collect all product JSON files under crawled_data/
    2. Partition into segments
    3. Build postings + vocab per segment
    4. Merge into final postings.bin, vocab.json, doc_map.json
    """
    if not CRAWLED_FOLDER.exists():
        raise FileNotFoundError(f"crawled_data folder not found at {CRAWLED_FOLDER}")

    files = list(CRAWLED_FOLDER.rglob("*.json"))
    total_files = len(files)
    if total_files == 0:
        print("No product files found under crawled_data/. Nothing to index.")
        return

    num_segments = MIN_SEGMENTS if total_files >= MIN_SEGMENTS else total_files
    chunk_size = math.ceil(total_files / num_segments)
    chunks = [files[i:i+chunk_size] for i in range(0, total_files, chunk_size)]
    if len(chunks) > num_segments:
        while len(chunks) > num_segments:
            chunks[-2].extend(chunks[-1])
            chunks.pop()

    print(f"Total files: {total_files}, segments: {len(chunks)}")

    global_doc_id = 0
    segment_vocab_files = []
    segment_postings_files = []
    segment_docmap_files = []

    # ----------------------- Build Segments ----------------------
    for si, chunk in enumerate(chunks):
        print(f"Building segment {si+1}/{len(chunks)} with {len(chunk)} files...")
        postings: Dict[str, List[Tuple[int, float]]] = {}
        doc_map_segment: Dict[str, dict] = {}

        for fpath in chunk:
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception as e:
                print(f"Failed to load {fpath}: {e}")
                continue

            html = data.get("content", "")
            url = data.get("url", str(fpath))
            soup = BeautifulSoup(html, "html.parser")
            token_freqs: Dict[str, FrequencyList] = get_token_frequencies(soup)
            doc_len = sum(fl.total for fl in token_freqs.values())

            doc_id = global_doc_id
            doc_map_segment[str(doc_id)] = {
                "id": doc_id,
                "url": url,
                "total_tokens": doc_len,
                "product": data.get("product", None)
            }

            for token, fl in token_freqs.items():
                weighted_points = fl.normal * 1 + fl.title * 5 + fl.heading * 10
                tf_score = weighted_points / max(1, doc_len)
                postings.setdefault(token, []).append((doc_id, float(tf_score)))

            global_doc_id += 1

        seg_post = Path(SEG_POSTINGS.format(i=si))
        seg_vocab = Path(SEG_VOCAB.format(i=si))
        seg_docmap = Path(SEG_DOCMAP.format(i=si))
        write_segment_postings_and_vocab(postings, seg_post, seg_vocab)
        with open(seg_docmap, "w", encoding="utf-8") as df:
            json.dump(doc_map_segment, df, indent=2)

        segment_vocab_files.append(seg_vocab)
        segment_postings_files.append(seg_post)
        segment_docmap_files.append(seg_docmap)
        print(f"Segment {si+1} written: {seg_post} {seg_vocab} {seg_docmap}")

    # ----------------------- Merge Segments ----------------------
    print("Merging segments into final postings.bin ...")
    final_doc_map: Dict[int, dict] = {}
    for seg_dm in segment_docmap_files:
        with open(seg_dm, "r", encoding="utf-8") as f:
            seg_map = json.load(f)
            final_doc_map.update({int(k): v for k, v in seg_map.items()})

    union_tokens = set()
    segment_vocabs = []
    for seg_vocab in segment_vocab_files:
        with open(seg_vocab, "r", encoding="utf-8") as vf:
            sv = json.load(vf)
            segment_vocabs.append(sv)
            union_tokens.update(sv.keys())

    with open(POSTINGS_FINAL, "wb") as final_pf:
        final_vocab = {}
        cur_offset = 0

        for token in sorted(union_tokens):
            merged_list: List[Tuple[int, float]] = []
            for si, sv in enumerate(segment_vocabs):
                if token not in sv:
                    continue
                seg_post_path = segment_postings_files[si]
                seg_token_meta = sv[token]
                with open(seg_post_path, "rb") as spf:
                    spf.seek(seg_token_meta["offset"])
                    raw = spf.read(seg_token_meta["length"])
                i = 0
                prev_doc = 0
                while i < len(raw):
                    val = 0
                    while True:
                        byte = raw[i]
                        i += 1
                        if byte >= 128:
                            val = (val << 7) | (byte - 128)
                            break
                        else:
                            val = (val << 7) | byte
                    delta = val
                    doc_id = prev_doc + delta
                    prev_doc = doc_id
                    tf = struct.unpack("<f", raw[i:i+4])[0]
                    i += 4
                    merged_list.append((doc_id, tf))

            merged_list.sort(key=lambda x: x[0])
            token_bytes = bytearray()
            prev = 0
            for doc_id, tf in merged_list:
                delta = doc_id - prev
                token_bytes.extend(vb_encode_number(delta))
                token_bytes.extend(struct.pack("<f", float(tf)))
                prev = doc_id

            final_pf.write(token_bytes)
            final_vocab[token] = {"offset": cur_offset, "length": len(token_bytes)}
            cur_offset += len(token_bytes)

    with open(VOCAB_FINAL, "w", encoding="utf-8") as vf:
        json.dump(final_vocab, vf, indent=2)

    final_doc_map_strkeys = {str(k): v for k, v in final_doc_map.items()}
    with open(DOCMAP_FINAL, "w", encoding="utf-8") as df:
        json.dump(final_doc_map_strkeys, df, indent=2)

    # ----------------------- Analytics ----------------------
    N = len(final_doc_map)
    unique_tokens = len(final_vocab)
    size_kb = os.path.getsize(POSTINGS_FINAL) / 1024.0
    print("\nIndex Analytics")
    print(f"Indexed documents: {N}")
    print(f"Unique tokens (words + n-grams): {unique_tokens}")
    print(f"Postings file size: {size_kb:.2f} KB")

    with open("index_deliverables.txt", "w", encoding="utf-8") as rep:
        rep.write("Inverted Index Analytics\n")
        rep.write(f"Indexed documents: {N}\n")
        rep.write(f"Unique tokens (words + n-grams): {unique_tokens}\n")
        rep.write(f"Postings file size: {size_kb:.2f} KB\n")
        rep.write(f"Vocab file: {VOCAB_FINAL}\n")
        rep.write(f"Doc map: {DOCMAP_FINAL}\n")
    print("Deliverables written to index_deliverables.txt")


if __name__ == "__main__":
    build_index()
