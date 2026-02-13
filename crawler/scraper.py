# crawler/scraper.py

import os
import json
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup

from indexer_searcher.ProductSchema import Product

BASE_OUTPUT = "crawled_data"

if not os.path.exists(BASE_OUTPUT):
    os.makedirs(BASE_OUTPUT)


def domain_folder(url: str) -> str:
    """Return folder name based on domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    folder = os.path.join(BASE_OUTPUT, domain)
    os.makedirs(folder, exist_ok=True)
    return folder


def slugify(url: str) -> str:
    """Convert URL path into a safe filename."""
    parsed = urlparse(url)
    slug = parsed.path.replace("/", "_").strip("_")
    if not slug:
        slug = "index"
    return slug + ".json"


def is_product_page(url: str) -> bool:
    """Detect Sweetwater or Guitar Center product pages."""
    parsed = urlparse(url)

    if "sweetwater.com" in parsed.netloc:
        return "/store/detail/" in parsed.path

    if "guitarcenter.com" in parsed.netloc:
        return parsed.path.startswith("/p/")

    return False


def is_category_page(url: str) -> bool:
    """Detect category/listing pages that contain product links."""
    parsed = urlparse(url)

    if "sweetwater.com" in parsed.netloc:
        # e.g. /c695--Electric_Guitars or other category/store pages
        return "/c" in parsed.path or "/store/" in parsed.path

    if "guitarcenter.com" in parsed.netloc:
        # e.g. /guitars/ or /Electric-Guitars
        path = parsed.path
        return "/guitars/" in path or "Electric-Guitars" in path

    return False


def extract_product(url: str, soup: BeautifulSoup) -> Product:
    """Extract product information from a Sweetwater or Guitar Center product page."""
    product = Product(url=url, html=str(soup))

    # ---------------- Sweetwater ----------------
    if "sweetwater.com" in url:
        name_tag = soup.find("h1")
        if name_tag:
            product.name = name_tag.get_text(strip=True)

        brand_tag = soup.find("a", attrs={"data-qa": "manufacturer-link"})
        if brand_tag:
            product.brand = brand_tag.get_text(strip=True)

        price_tag = soup.find(attrs={"data-qa": "price"})
        if price_tag:
            try:
                product.price = float(
                    price_tag.get_text(strip=True)
                    .replace("$", "")
                    .replace(",", "")
                )
            except Exception:
                pass

        rating_tag = soup.find(attrs={"data-qa": "rating-value"})
        if rating_tag:
            try:
                product.rating = float(rating_tag.get_text(strip=True))
            except Exception:
                pass

        review_tag = soup.find(attrs={"data-qa": "review-count"})
        if review_tag:
            try:
                product.num_reviews = int(
                    review_tag.get_text(strip=True).split()[0]
                )
            except Exception:
                pass

        desc_tag = soup.find("div", attrs={"data-qa": "description"})
        if desc_tag:
            product.description = desc_tag.get_text(" ", strip=True)

        specs = {}
        for row in soup.select("table tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                val = cols[1].get_text(strip=True)
                if key and val:
                    specs[key] = val
        product.specs = specs

        img_tag = soup.find("img", attrs={"data-qa": "main-image"})
        if img_tag and img_tag.get("src"):
            product.image = img_tag["src"]

    # ---------------- Guitar Center ----------------
    elif "guitarcenter.com" in url:
        name_tag = soup.find("h1", {"data-testid": "product-title"})
        if name_tag:
            product.name = name_tag.get_text(strip=True)

        brand_tag = soup.find("a", {"data-testid": "brand-link"})
        if brand_tag:
            product.brand = brand_tag.get_text(strip=True)

        price_tag = soup.find("span", {"data-testid": "price"})
        if price_tag:
            try:
                product.price = float(
                    price_tag.get_text(strip=True)
                    .replace("$", "")
                    .replace(",", "")
                )
            except Exception:
                pass

        rating_tag = soup.find("span", {"data-testid": "rating-value"})
        if rating_tag:
            try:
                product.rating = float(rating_tag.get_text(strip=True))
            except Exception:
                pass

        review_tag = soup.find("span", {"data-testid": "review-count"})
        if review_tag:
            try:
                product.num_reviews = int(
                    review_tag.get_text(strip=True).split()[0]
                )
            except Exception:
                pass

        desc_tag = soup.find("div", {"data-testid": "description"})
        if desc_tag:
            product.description = desc_tag.get_text(" ", strip=True)

        specs = {}
        for row in soup.select("table tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                val = cols[1].get_text(strip=True)
                if key and val:
                    specs[key] = val
        product.specs = specs

        img_tag = soup.find("img", {"data-testid": "main-image"})
        if img_tag and img_tag.get("src"):
            product.image = img_tag["src"]

    return product


def scraper(url, resp):
    """
    Main scraper entry point used by Worker.

    Returns:
        - Product object (if product page, and also writes JSON to crawled_data/)
        - list[str] of URLs (if category page)
        - [] otherwise
    """
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return []

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    # Product page → extract + save
    if is_product_page(url):
        product = extract_product(url, soup)

        folder = domain_folder(url)
        fname = slugify(url)
        out_path = os.path.join(folder, fname)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(product.to_json(), f, indent=2)

        return product

    # Category page → return product + category links
    if is_category_page(url):
        links = []
        for a in soup.find_all("a", href=True):
            abs_url = urljoin(url, a["href"])
            clean_url, _ = urldefrag(abs_url)
            if is_product_page(clean_url) or is_category_page(clean_url):
                links.append(clean_url)
        return links

    # Everything else → ignore
    return []
