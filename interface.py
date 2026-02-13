# interface.py

import sys
from pathlib import Path

# Make sure local packages are importable
ROOT = Path(__file__).parent
sys.path.append(str(ROOT))

from crawler.config import Config
from crawler.frontier import Frontier
from crawler.worker import Worker
from indexer_searcher.indexer import build_index
from indexer_searcher.searcher import Searcher


def run_crawler():
    config = Config()
    frontier = Frontier(save_file=config.save_file)

    # Seed URLs if frontier is empty
    if frontier.is_empty():
        for url in config.seed_urls:
            frontier.add_url(url)

    workers = []
    for i in range(config.threads_count):
        w = Worker(worker_id=i, config=config, frontier=frontier)
        workers.append(w)
        w.start()

    for w in workers:
        w.join()

    print("Crawling complete.")


def run_indexer():
    print("Building index from crawled_data/ ...")
    build_index()
    print("Indexing complete.")


def run_search():
    searcher = Searcher()
    print("Enter queries (empty line to exit):")
    while True:
        query = input("> ").strip()
        if not query:
            break

        results = searcher.search(query, k=10)
        if not results:
            print("No results.")
            continue

        for rank, (doc_id, score, meta) in enumerate(results, start=1):
            url = meta.get("url", "UNKNOWN")
            product = meta.get("product") or {}
            name = product.get("name") or "(no name)"
            brand = product.get("brand") or ""
            price = product.get("price")
            price_str = f"${price:.2f}" if isinstance(price, (int, float)) else ""
            print(f"{rank}. {name} {brand} {price_str} [{score:.4f}]")
            print(f"   {url}")
        print()


def main():
    while True:
        print("\n==============================")
        print("        MusicMatcher")
        print("==============================")
        print("1. Crawl products")
        print("2. Build index")
        print("3. Search")
        print("4. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            run_crawler()
        elif choice == "2":
            run_indexer()
        elif choice == "3":
            run_search()
        elif choice == "4":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please enter 1–4.")


if __name__ == "__main__":
    main()
