#indexer_searcher/searcher.py
import json
import struct
import math
import time
from typing import List
from functools import lru_cache
from nltk.stem import PorterStemmer

"""
Searcher with proper stemming for Boolean AND and Ranked search.

Features:
- Disk-backed postings reading (varbyte decoding)
- Ranked search using tf-idf
- Boolean AND search
- Query stemming to match indexed tokens
- Top 10 results printed
- Query timings displayed
"""

VOCAB_FILE = "vocab.json"
DOC_MAP_FILE = "doc_map.json"
POSTINGS_FILE = "postings.bin"

# ----------------------- VarByte Decoding ----------------------
def vb_decode_all(raw: bytes) -> List[int]:
    vals = []
    i = 0
    while i < len(raw):
        v = 0
        while True:
            byte = raw[i]
            i += 1
            if byte >= 128:
                v = (v << 7) | (byte - 128)
                break
            else:
                v = (v << 7) | byte
        vals.append(v)
    return vals


# ----------------------- Searcher Class ----------------------
class Searcher:
    def __init__(self, vocab_file=VOCAB_FILE, doc_map_file=DOC_MAP_FILE, postings_file=POSTINGS_FILE):
        with open(vocab_file, "r", encoding="utf-8") as vf:
            self.vocab = json.load(vf)
        with open(doc_map_file, "r", encoding="utf-8") as df:
            raw = json.load(df)
            self.doc_map = {int(k): v for k, v in raw.items()}
        self.N = len(self.doc_map)
        self.postings_file = postings_file
        self._fp = open(self.postings_file, "rb")
        self.stemmer = PorterStemmer()  # Initialize stemmer

    def close(self):
        if self._fp:
            self._fp.close()
            self._fp = None

    @lru_cache(maxsize=16)
    def read_postings(self, token: str):
        meta = self.vocab.get(token)
        if not meta:
            return []
        self._fp.seek(meta["offset"])
        raw = self._fp.read(meta["length"])
        out = []
        i = 0
        prev = 0
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
            doc_id = prev + delta
            prev = doc_id
            tf = struct.unpack("<f", raw[i:i+4])[0]
            i += 4
            out.append((doc_id, tf))
        return out

    def idf(self, token: str) -> float:
        postings = self.read_postings(token)
        df = len(postings)
        if df == 0:
            return 0.0
        return math.log(self.N / df)

    def ranked_search(self, query_tokens: List[str], k: int = 10):
        scores = {}
        for token in query_tokens:
            if token not in self.vocab:
                continue
            idf_val = self.idf(token)
            postings = self.read_postings(token)
            for doc_id, tf in postings:
                scores[doc_id] = scores.get(doc_id, 0.0) + tf * idf_val
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self.doc_map[d]["url"], sc) for d, sc in ranked[:k]]

    def boolean_and(self, query_tokens: List[str]):
        if not query_tokens:
            return []
        sets = []
        for token in query_tokens:
            postings = self.read_postings(token)
            if not postings:
                return []
            sets.append({doc_id for doc_id, _ in postings})
        result_set = set.intersection(*sets) if sets else set()
        return [self.doc_map[d]["url"] for d in sorted(result_set)]


# ----------------------- Interactive Demo ----------------------
if __name__ == "__main__":
    s = Searcher()
    try:
        while True:
            q = input("Query (empty to quit): ").strip()
            if not q:
                break

            # ----------------------- Stem the query -----------------------
            toks = [s.stemmer.stem(t.lower()) for t in q.split()]

            mode = input("Mode (ranked/and) [ranked]: ").strip() or "ranked"

            start_time = time.time()  # Start timer
            if mode == "and":
                res = s.boolean_and(toks)
                elapsed = time.time() - start_time
                print(f"Boolean AND search: {len(res)} results (time={elapsed:.4f} sec)")
                for u in res[:10]:
                    print(u)
            else:
                res = s.ranked_search(toks, k=10)
                elapsed = time.time() - start_time
                print(f"Top 10 results for query: '{q}' ({elapsed:.4f} sec)")
                if res:
                    for u, sc in res:
                        print(f"{u} (score={sc:.4f})")
                else:
                    print("No results found.")
    finally:
        s.close()
