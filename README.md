# MusicMatcher

MusicMatcher is a guitar search and recommendation prototype. It supports:

- crawling product pages (Sweetwater + Guitar Center)
- indexing product content
- ranked search with context + personal-model reranking
- a user-facing web UI for demo scenarios

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Fast Demo Path (recommended)

This path does not require running the live crawler.

```bash
python demo_seed.py
python -c "from indexer_searcher.indexer import build_index; build_index()"
python webapp.py
```

Open: http://127.0.0.1:5000

Inside the UI:
1. Click `Create Demo Dataset` (safe if already seeded)
2. Click `Build / Rebuild Index`
3. Run two scenarios and change context/profile values to show ranking changes

## 3) Optional Live Crawl Path

```bash
python interface.py
```

Use menu option `1` to crawl, `2` to build index, `3` to search.

Note: live crawling is still slower and riskier than demo dataset flow.

## 4) Demo Scenario Ideas

- Scenario A: Query `stratocaster`, budget `300-900`, level `beginner`
- Scenario B: Same query, budget `1000-2200`, level `advanced`, preferred brand `Fender`

These should produce ranking changes that are visible in the UI.

## 5) Project Structure

- `crawler/` -> frontier, robots, scraping, workers
- `indexer_searcher/` -> tokenizer, index builder, search + reranking
- `webapp.py` -> user-facing Flask demo UI
- `demo_seed.py` -> deterministic local demo dataset

