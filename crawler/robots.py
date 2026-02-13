# crawler/robots.py

import requests
from urllib.parse import urlparse


class RobotsManager:
    """
    Minimal robots.txt manager:
    - Caches robots.txt per domain
    - Parses Disallow rules
    - Optionally parses Crawl-delay
    """

    def __init__(self, default_delay: float = 1.0):
        self.cache = {}          # domain -> {"disallow": [...], "delay": float}
        self.default_delay = default_delay

    def _fetch_robots(self, domain: str):
        """Fetch and parse robots.txt for a domain, cache result."""
        if domain in self.cache:
            return self.cache[domain]

        url = f"https://{domain}/robots.txt"
        disallow = []
        delay = self.default_delay

        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                for raw_line in resp.text.splitlines():
                    line = raw_line.strip()
                    lower = line.lower()

                    if lower.startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            disallow.append(path)

                    elif lower.startswith("crawl-delay:"):
                        try:
                            delay = float(line.split(":", 1)[1].strip())
                        except Exception:
                            pass
        except Exception:
            # If robots.txt can't be fetched, assume no extra restrictions
            pass

        info = {"disallow": disallow, "delay": delay}
        self.cache[domain] = info
        return info

    def allowed(self, url: str) -> bool:
        """Return True if URL is allowed by robots.txt."""
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path

        info = self._fetch_robots(domain)
        for rule in info["disallow"]:
            # Exact "/" disallow means nothing is allowed
            if rule == "/":
                return False
            if path.startswith(rule):
                return False

        return True

    def get_delay(self, url: str) -> float:
        """Return crawl-delay for this URL's domain (or default)."""
        parsed = urlparse(url)
        domain = parsed.netloc
        info = self._fetch_robots(domain)
        return info["delay"]
