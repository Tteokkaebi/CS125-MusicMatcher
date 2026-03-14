# webapp.py

from pathlib import Path
from threading import Lock

from flask import Flask, render_template, request, session, redirect, url_for

from indexer_searcher.searcher import Searcher
from indexer_searcher.indexer import build_index
from demo_seed import main as seed_demo_data

app = Flask(__name__)
app.secret_key = "musicmatcher-final-demo-key"

_INDEX_FILES = [Path("vocab.json"), Path("doc_map.json"), Path("postings.bin")]
_SEARCHER = None
_SEARCH_LOCK = Lock()


def has_index_files() -> bool:
    return all(path.exists() for path in _INDEX_FILES)


def get_searcher(force_reload: bool = False):
    global _SEARCHER
    with _SEARCH_LOCK:
        if force_reload and _SEARCHER is not None:
            _SEARCHER.close()
            _SEARCHER = None

        if _SEARCHER is None and has_index_files():
            _SEARCHER = Searcher()

        return _SEARCHER


def _parse_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _profile():
    if "saved_brands" not in session:
        session["saved_brands"] = []
    return session["saved_brands"]


@app.route("/", methods=["GET", "POST"])
def home():
    saved_brands = _profile()
    notice = None
    results = []

    form_data = {
        "query": "",
        "budget_min": "",
        "budget_max": "",
        "preferred_brand": "",
        "experience_level": "",
        "retailer": "",
        "top_k": "10",
        "remember_brand": False,
    }

    if request.method == "POST":
        action = request.form.get("action", "search")

        if action == "seed_demo":
            seed_demo_data()
            notice = "Demo dataset created in crawled_data/demo/."
        elif action == "rebuild_index":
            try:
                build_index()
                get_searcher(force_reload=True)
                notice = "Index rebuilt from crawled_data/."
            except Exception as exc:
                notice = f"Index build failed: {exc}"
        elif action == "clear_profile":
            session["saved_brands"] = []
            saved_brands = []
            notice = "Saved brand profile was reset."
        else:
            form_data = {
                "query": request.form.get("query", "").strip(),
                "budget_min": request.form.get("budget_min", "").strip(),
                "budget_max": request.form.get("budget_max", "").strip(),
                "preferred_brand": request.form.get("preferred_brand", "").strip(),
                "experience_level": request.form.get("experience_level", "").strip(),
                "retailer": request.form.get("retailer", "").strip(),
                "top_k": request.form.get("top_k", "10").strip(),
                "remember_brand": request.form.get("remember_brand") == "on",
            }

            preferred_brand = form_data["preferred_brand"]
            if form_data["remember_brand"] and preferred_brand:
                lower_saved = [b.lower() for b in saved_brands]
                if preferred_brand.lower() not in lower_saved:
                    saved_brands.append(preferred_brand)
                    session["saved_brands"] = saved_brands

            top_k = int(form_data["top_k"] or "10")
            top_k = max(1, min(25, top_k))

            context = {
                "budget_min": _parse_float(form_data["budget_min"]),
                "budget_max": _parse_float(form_data["budget_max"]),
                "experience_level": form_data["experience_level"],
                "retailer": form_data["retailer"],
            }
            preferences = {
                "preferred_brand": preferred_brand,
                "saved_brands": saved_brands,
            }

            searcher = get_searcher()
            if searcher is None:
                notice = "Index files not found. Seed demo data and rebuild index first."
            else:
                raw_results = searcher.search(
                    query=form_data["query"],
                    k=top_k,
                    preferences=preferences,
                    context=context,
                )

                for rank, (_, score, meta) in enumerate(raw_results, start=1):
                    product = meta.get("product") or {}
                    results.append(
                        {
                            "rank": rank,
                            "name": product.get("name") or "(no name)",
                            "brand": product.get("brand") or "",
                            "price": product.get("price"),
                            "rating": product.get("rating"),
                            "reviews": product.get("num_reviews"),
                            "url": meta.get("url") or "",
                            "score": score,
                            "why": meta.get("why") or [],
                        }
                    )

    return render_template(
        "index.html",
        results=results,
        notice=notice,
        saved_brands=saved_brands,
        form=form_data,
        has_index=has_index_files(),
    )


@app.get("/healthz")
def healthz():
    return {"ok": True, "has_index": has_index_files()}


if __name__ == "__main__":
    app.run(debug=True)
