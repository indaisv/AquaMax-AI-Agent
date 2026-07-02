"""Product catalog business logic service."""

from __future__ import annotations

from src.database.connection import get_session
from src.database.repository import ProductRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProductService:
    """Business logic for product catalog operations."""

    def list_products(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all products with pagination."""
        try:
            with get_session() as session:
                repo = ProductRepository(session)
                products = repo.list_all(limit=limit, offset=offset)
                return [p.to_dict() for p in products]
        except Exception as e:
            logger.error("Failed to list products: %s", e)
            return []

    def search_products(self, query: str, category: str | None = None, max_price: float | None = None) -> list[dict]:
        """Search products by query."""
        try:
            with get_session() as session:
                repo = ProductRepository(session)
                products = repo.search(query, category=category, max_price=max_price)
                return [p.to_dict() for p in products]
        except Exception as e:
            logger.error("Failed to search products: %s", e)
            return []

    def get_product(self, product_id: int) -> dict | None:
        """Get a single product by ID."""
        try:
            with get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_id(product_id)
                return product.to_dict() if product else None
        except Exception as e:
            logger.error("Failed to get product: %s", e)
            return None

    def get_categories(self) -> list[str]:
        """Get all distinct product categories."""
        try:
            with get_session() as session:
                from sqlalchemy import distinct
                from src.database.models import Product
                result = session.query(distinct(Product.category)).all()
                return [r[0] for r in result if r[0]]
        except Exception as e:
            logger.error("Failed to get categories: %s", e)
            return []
