# crawler/worker.py

from threading import Thread
import time

from utils.download import download
from utils import get_logger

from url_filters import is_valid
from robots import RobotsManager
import scraper


class Worker(Thread):
    """
    MusicMatcher Worker:
    - Pulls URLs from the frontier
    - Downloads pages
    - Applies URL validation
    - Calls scraper (product or category)
    - Adds new URLs to frontier
    - Respects robots.txt crawl-delay
    """

    def __init__(self, worker_id, config, frontier):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.robots = RobotsManager()

    def run(self):
        while True:
            url = self.frontier.get_tbd_url()
            if not url:
                self.logger.info("Frontier empty. Worker stopping.")
                break

            # Validate URL before downloading
            if not is_valid(url):
                self.logger.info(f"Skipping invalid URL: {url}")
                self.frontier.mark_url_complete(url)
                continue

            # Download page
            resp = download(url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}."
            )

            # Scrape page
            result = scraper.scraper(url, resp)

            # If scraper returns a Product object → nothing to add to frontier
            if isinstance(result, list):
                # Category page → add links
                for link in result:
                    if is_valid(link):
                        self.frontier.add_url(link)

            # Mark URL as processed
            self.frontier.mark_url_complete(url)

            # Respect robots.txt crawl-delay
            delay = self.robots.get_delay(url)
            time.sleep(delay)

        self.logger.info(f"Worker-{self.worker_id} finished.")
