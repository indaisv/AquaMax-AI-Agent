"""Product catalog search tool."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repository import ProductRepository
from src.utils.helpers import sanitize_input
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.database.models import Product

logger = get_logger(__name__)


@tool
def search_products(query: str, category: str | None = None, max_price: float | None = None) -> str:
    """Search the AquaMax product catalog for rehabilitation and physiotherapy equipment.

    Use this tool when the user is looking for equipment, mentions a condition, or asks for product recommendations.
    Returns a formatted list of matching products with key details.

    Args:
        query: Search terms (condition, equipment type, body part, etc.)
        category: Optional filter by category (e.g., "Electrotherapy", "Mobility Aids")
        max_price: Optional maximum price filter in INR
    """
    query = sanitize_input(query)
    if not query or len(query) < 2:
        return "Please provide a more specific search query (at least 2 characters)."

    try:
        with get_session() as session:
            repo = ProductRepository(session)
            
            # Split query into keywords for better matching
            keywords = [kw.strip() for kw in query.split() if len(kw.strip()) >= 2]
            if not keywords:
                keywords = [query]
            
            # Try keyword search first
            results: list[Product] = repo.search_by_keywords(keywords, category=category, max_price=max_price)
            
            # Fallback to phrase search if keyword search returns nothing
            if not results:
                results = repo.search(query, category=category, max_price=max_price)
            
            if not results:
                # Try condition-based search with individual keywords
                for kw in keywords:
                    condition_results = repo.filter_by_condition(kw)
                    if condition_results:
                        results.extend(condition_results)
                # Deduplicate
                seen = set()
                results = [p for p in results if not (p.id in seen or seen.add(p.id))]
            
            if not results:
                return (
                    f"No products found for '{query}'.\n"
                    "Try searching with different keywords like:\n"
                    "- Body part: knee, back, shoulder, ankle\n"
                    "- Equipment type: TENS, ultrasound, walker, wheelchair\n"
                    "- Condition: arthritis, stroke, sports injury, chronic pain"
                )

            lines = [f"Found {len(results)} product(s) for '{query}':\n"]
            for i, p in enumerate(results[:10], 1):
                data = p.to_dict()
                features = ", ".join(data["features"][:3]) if data["features"] else ""
                lines.append(
                    f"{i}. **{data['name']}** (SKU: {data['sku']})\n"
                    f"   - Category: {data['category']} | Subcategory: {data['subcategory'] or 'N/A'}\n"
                    f"   - Price: ₹{data['price']:,.2f} | Rating: {data['rating']}/5.0 | Stock: {data['stock']}\n"
                    f"   - Features: {features}\n"
                    f"   - {data['description'][:120]}...\n"
                )

            return "\n".join(lines)

    except Exception as e:
        logger.error("Product search failed: %s", e)
        return f"Sorry, the product search encountered an error. Please try again. (Error: {type(e).__name__})"
