# indexer_searcher/product.py

from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class Product:
    # Core identifiers
    url: str
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None

    # Commerce attributes
    price: Optional[float] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None

    # Content
    description: Optional[str] = None
    specs: Dict[str, str] = field(default_factory=dict)
    image: Optional[str] = None

    # Raw HTML (for indexing)
    html: Optional[str] = None

    def to_json(self):
        """Convert to a JSON‑serializable dict."""
        return {
            "url": self.url,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "rating": self.rating,
            "num_reviews": self.num_reviews,
            "description": self.description,
            "specs": self.specs,
            "image": self.image,
            "content": self.html,   # indexer expects this key
            "product": {
                "name": self.name,
                "brand": self.brand,
                "category": self.category,
                "price": self.price,
                "rating": self.rating,
                "num_reviews": self.num_reviews,
                "specs": self.specs,
                "description": self.description,
                "image": self.image
            }
        }
