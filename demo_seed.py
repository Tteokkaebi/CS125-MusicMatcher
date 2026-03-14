# demo_seed.py

import json
from pathlib import Path


DEMO_PRODUCTS = [
    {
        "url": "https://www.sweetwater.com/store/detail/PlayerStrat--fender-player-stratocaster",
        "name": "Fender Player Stratocaster",
        "brand": "Fender",
        "price": 849.99,
        "rating": 4.7,
        "num_reviews": 211,
        "description": "Versatile strat-style electric guitar for beginner and intermediate players.",
        "genre": "rock blues pop",
    },
    {
        "url": "https://www.sweetwater.com/store/detail/AffiTele--fender-affinity-telecaster",
        "name": "Squier Affinity Telecaster",
        "brand": "Squier",
        "price": 299.99,
        "rating": 4.4,
        "num_reviews": 143,
        "description": "Budget tele-style guitar with solid value.",
        "genre": "country rock indie",
    },
    {
        "url": "https://www.sweetwater.com/store/detail/SECustom24--prs-se-custom-24",
        "name": "PRS SE Custom 24",
        "brand": "PRS",
        "price": 899.99,
        "rating": 4.8,
        "num_reviews": 124,
        "description": "Balanced tone with humbuckers for modern rock and fusion.",
        "genre": "rock fusion metal",
    },
    {
        "url": "https://www.guitarcenter.com/p/Gibson-Les-Paul-Studio.gc",
        "name": "Gibson Les Paul Studio",
        "brand": "Gibson",
        "price": 1699.99,
        "rating": 4.6,
        "num_reviews": 98,
        "description": "Classic high-output electric guitar with warm sustain.",
        "genre": "rock hard-rock classic",
    },
    {
        "url": "https://www.guitarcenter.com/p/Ibanez-RG421.gc",
        "name": "Ibanez RG421",
        "brand": "Ibanez",
        "price": 449.99,
        "rating": 4.5,
        "num_reviews": 156,
        "description": "Fast neck and aggressive tone, popular for metal.",
        "genre": "metal rock shred",
    },
    {
        "url": "https://www.guitarcenter.com/p/Yamaha-Pacifica-112V.gc",
        "name": "Yamaha Pacifica 112V",
        "brand": "Yamaha",
        "price": 329.99,
        "rating": 4.7,
        "num_reviews": 274,
        "description": "Reliable beginner guitar with great quality control.",
        "genre": "beginner rock blues",
    },
    {
        "url": "https://www.sweetwater.com/store/detail/RevstarRSS20--yamaha-revstar-rss20",
        "name": "Yamaha Revstar RSS20",
        "brand": "Yamaha",
        "price": 849.99,
        "rating": 4.8,
        "num_reviews": 66,
        "description": "Modern take on a classic double-cut style.",
        "genre": "indie rock alt",
    },
    {
        "url": "https://www.guitarcenter.com/p/Fender-American-Professional-II-Stratocaster.gc",
        "name": "Fender American Professional II Stratocaster",
        "brand": "Fender",
        "price": 1799.99,
        "rating": 4.9,
        "num_reviews": 82,
        "description": "Premium strat with polished feel and classic tone.",
        "genre": "blues funk rock",
    },
    {
        "url": "https://www.sweetwater.com/store/detail/LTD-EC256--esp-ltd-ec-256",
        "name": "ESP LTD EC-256",
        "brand": "ESP LTD",
        "price": 549.99,
        "rating": 4.6,
        "num_reviews": 91,
        "description": "Single-cut style with high-gain friendly humbuckers.",
        "genre": "metal hard-rock",
    },
    {
        "url": "https://www.guitarcenter.com/p/Jackson-Dinky-JS22.gc",
        "name": "Jackson Dinky JS22",
        "brand": "Jackson",
        "price": 239.99,
        "rating": 4.3,
        "num_reviews": 137,
        "description": "Low-cost metal-focused electric guitar.",
        "genre": "metal beginner",
    },
    {
        "url": "https://www.sweetwater.com/store/detail/SilverSkySE--prs-se-silver-sky",
        "name": "PRS SE Silver Sky",
        "brand": "PRS",
        "price": 849.00,
        "rating": 4.9,
        "num_reviews": 103,
        "description": "Vintage-inspired feel with modern build consistency.",
        "genre": "blues pop rock",
    },
    {
        "url": "https://www.guitarcenter.com/p/Epiphone-Les-Paul-Standard-50s.gc",
        "name": "Epiphone Les Paul Standard 50s",
        "brand": "Epiphone",
        "price": 699.00,
        "rating": 4.7,
        "num_reviews": 167,
        "description": "Affordable les-paul style guitar with thick tone.",
        "genre": "rock blues classic",
    },
]


def make_html(item: dict) -> str:
    title = item["name"]
    desc = item["description"]
    genre = item["genre"]
    price = item["price"]
    rating = item["rating"]
    reviews = item["num_reviews"]

    return (
        f"<html><head><title>{title}</title></head>"
        f"<body><h1>{title}</h1>"
        f"<h2>{item['brand']} electric guitar</h2>"
        f"<p>{desc}</p>"
        f"<p>Genres: {genre}</p>"
        f"<p>Price {price} dollars.</p>"
        f"<p>Rating {rating} from {reviews} reviews.</p>"
        f"</body></html>"
    )


def main():
    out_dir = Path("crawled_data") / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, item in enumerate(DEMO_PRODUCTS):
        payload = {
            "url": item["url"],
            "content": make_html(item),
            "product": {
                "name": item["name"],
                "brand": item["brand"],
                "category": "Electric Guitar",
                "price": item["price"],
                "rating": item["rating"],
                "num_reviews": item["num_reviews"],
                "specs": {},
                "description": item["description"],
                "image": None,
            },
        }

        fpath = out_dir / f"demo_{idx:02d}.json"
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    print(f"Wrote {len(DEMO_PRODUCTS)} demo items to {out_dir}")


if __name__ == "__main__":
    main()
