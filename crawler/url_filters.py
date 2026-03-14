# crawler/url_filters.py

from urllib.parse import urlparse, urldefrag

try:
    from .robots import RobotsManager
    from .scraper import is_product_page, is_category_page
except ImportError:
    from robots import RobotsManager
    from scraper import is_product_page, is_category_page

robots = RobotsManager()

ALLOWED_DOMAINS = {
    "sweetwater.com",
    "www.sweetwater.com",
    "guitarcenter.com",
    "www.guitarcenter.com",
}

BLOCKED_KEYWORDS = [
    "cart", "checkout", "account", "login", "signup",
    "search", "track", "privacy", "terms", "policy",
    "gift-card", "wishlist", "compare", "help", "support",
]


def is_valid(url: str) -> bool:
    """
    Determines whether a URL should be crawled by MusicMatcher.
    Enforces:
      - domain restrictions
      - robots.txt rules
      - junk URL filtering
      - product/category page filtering
    """
    if not url:
        return False

    # Remove fragments (#section)
    url, _ = urldefrag(url)
    parsed = urlparse(url)

    # Must be HTTP or HTTPS
    if parsed.scheme not in {"http", "https"}:
        return False

    # Domain restriction
    domain = parsed.netloc.lower()
    if domain not in ALLOWED_DOMAINS:
        return False

    # robots.txt enforcement
    if not robots.allowed(url):
        return False

    # Block junk URLs
    path = parsed.path.lower()
    if any(bad in path for bad in BLOCKED_KEYWORDS):
        return False

    # Allow only product or category pages
    if is_product_page(url) or is_category_page(url):
        return True

    return False
