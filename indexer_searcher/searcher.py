#indexer_searcher/searcher.py
import json
import struct
import math
import time
import re
from typing import List
from functools import lru_cache
from nltk.stem import PorterStemmer

"""
Searcher with stemming for ranked and boolean search.

Features:
- Disk-backed postings reading (varbyte decoding)
- Ranked search using tf-idf baseline
- Context and personal-model reweighting
- Boolean AND search
"""

VOCAB_FILE = "vocab.json"
DOC_MAP_FILE = "doc_map.json"
POSTINGS_FILE = "postings.bin"


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
        self.stemmer = PorterStemmer()

    def close(self):
        if self._fp:
            self._fp.close()
            self._fp = None

    def tokenize_query(self, query: str) -> List[str]:
        tokens = re.split(r"[^a-zA-Z0-9]+", (query or "").lower())
        return [self.stemmer.stem(t) for t in tokens if len(t) > 2]

    @lru_cache(maxsize=64)
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

    def _baseline_scores(self, query_tokens: List[str]):
        if not query_tokens:
            return {doc_id: 0.0 for doc_id in self.doc_map.keys()}

        scores = {}
        for token in query_tokens:
            if token not in self.vocab:
                continue
            idf_val = self.idf(token)
            postings = self.read_postings(token)
            for doc_id, tf in postings:
                scores[doc_id] = scores.get(doc_id, 0.0) + tf * idf_val
        return scores

    @staticmethod
    def _to_float(value):
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _rerank_with_context(self, doc_info, preferences, context):
        product = doc_info.get("product") or {}
        url = (doc_info.get("url") or "").lower()

        score_delta = 0.0
        reasons = []

        brand = (product.get("brand") or "").strip().lower()
        price = self._to_float(product.get("price"))
        rating = self._to_float(product.get("rating"))
        num_reviews = self._to_float(product.get("num_reviews"))

        budget_min = self._to_float(context.get("budget_min"))
        budget_max = self._to_float(context.get("budget_max"))
        if price is not None and budget_min is not None and budget_max is not None and budget_max >= budget_min:
            if budget_min <= price <= budget_max:
                width = max(1.0, budget_max - budget_min)
                center = (budget_min + budget_max) / 2.0
                closeness = 1.0 - min(abs(price - center) / (width / 2.0 + 1.0), 1.0)
                score_delta += 0.18 + 0.12 * closeness
                reasons.append("price fits budget")
            elif price > budget_max:
                score_delta -= 0.15
            else:
                score_delta -= 0.05

        if rating is not None:
            score_delta += max(0.0, min(0.20, (rating / 5.0) * 0.20))
            if rating >= 4.0:
                reasons.append("high rating")

        if num_reviews is not None and num_reviews > 0:
            score_delta += min(0.12, math.log1p(num_reviews) / 40.0)
            if num_reviews >= 25:
                reasons.append("strong review count")

        preferred_brand = (preferences.get("preferred_brand") or "").strip().lower()
        if preferred_brand and brand and preferred_brand in brand:
            score_delta += 0.20
            reasons.append("matches preferred brand")

        saved_brands = [b.strip().lower() for b in preferences.get("saved_brands", []) if b]
        if brand and any(sb in brand for sb in saved_brands):
            score_delta += 0.14
            reasons.append("matches your profile history")

        level = (context.get("experience_level") or "").strip().lower()
        if price is not None and level:
            if level == "beginner" and price <= 700:
                score_delta += 0.08
                reasons.append("beginner-friendly price")
            elif level == "intermediate" and 500 <= price <= 1500:
                score_delta += 0.08
                reasons.append("fits intermediate range")
            elif level == "advanced" and price >= 1000:
                score_delta += 0.08
                reasons.append("fits advanced range")

        retailer = (context.get("retailer") or "").strip().lower()
        if retailer and retailer in url:
            score_delta += 0.10
            reasons.append("matches retailer context")

        return score_delta, reasons

    def search(self, query: str, k: int = 10, preferences=None, context=None):
        preferences = preferences or {}
        context = context or {}

        query_tokens = self.tokenize_query(query)
        baseline_scores = self._baseline_scores(query_tokens)

        ranked = []
        for doc_id, base_score in baseline_scores.items():
            doc_info = self.doc_map.get(doc_id)
            if not doc_info:
                continue

            rerank_delta, reasons = self._rerank_with_context(doc_info, preferences, context)
            final_score = base_score + rerank_delta

            meta = {
                "url": doc_info.get("url", "UNKNOWN"),
                "product": doc_info.get("product") or {},
                "why": reasons[:3],
                "baseline_score": base_score,
                "rerank_delta": rerank_delta,
            }
            ranked.append((doc_id, final_score, meta))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:k]

    def ranked_search(self, query_tokens: List[str], k: int = 10):
        scores = self._baseline_scores(query_tokens)
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

            mode = input("Mode (ranked/and) [ranked]: ").strip() or "ranked"
            start_time = time.time()

            if mode == "and":
                toks = s.tokenize_query(q)
                res = s.boolean_and(toks)
                elapsed = time.time() - start_time
                print(f"Boolean AND search: {len(res)} results (time={elapsed:.4f} sec)")
                for u in res[:10]:
                    print(u)
            else:
                res = s.search(q, k=10)
                elapsed = time.time() - start_time
                print(f"Top 10 results for query: '{q}' ({elapsed:.4f} sec)")
                if res:
                    for _, sc, meta in res:
                        print(f"{meta.get('url')} (score={sc:.4f})")
                else:
                    print("No results found.")
    finally:
        s.close()
