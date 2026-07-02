"""Product comparison tool."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repository import ProductRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def compare_products(product_ids: str) -> str:
    """Compare two or more products side-by-side with highlighted differences.

    Use this tool when the user asks to compare specific products, wants to see differences,
    or is deciding between multiple options. Pass product IDs as a comma-separated string.

    Args:
        product_ids: Comma-separated list of product IDs (e.g., "1,2,3")
    """
    try:
        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
        if len(ids) < 2:
            return "Please provide at least 2 product IDs to compare (e.g., '1,2')."
        if len(ids) > 5:
            return "Please compare no more than 5 products at once for clarity."

        with get_session() as session:
            repo = ProductRepository(session)
            products = repo.get_by_ids(ids)

            if not products:
                return f"No products found with IDs: {ids}. Please verify the product IDs."

            # Sort by provided order
            id_order = {pid: idx for idx, pid in enumerate(ids)}
            products = sorted(products, key=lambda p: id_order.get(p.id, 999))

            # Build comparison table
            lines = ["## Product Comparison\n"]

            # Header row
            names = [p.name for p in products]
            lines.append("| Feature | " + " | ".join(names) + " |")
            lines.append("|" + "|".join(["---"] * (len(products) + 1)) + "|")

            # Price
            prices = [f"₹{p.price:,.2f}" for p in products]
            min_price = min(p.price for p in products)
            price_cells = [f"**{pr}**" if p.price == min_price else pr for p, pr in zip(products, prices)]
            lines.append("| Price | " + " | ".join(price_cells) + " |")

            # Rating
            ratings = [f"{p.rating}/5.0" for p in products]
            max_rating = max(p.rating for p in products)
            rating_cells = [f"**{r}**" if p.rating == max_rating else r for p, r in zip(products, ratings)]
            lines.append("| Rating | " + " | ".join(rating_cells) + " |")

            # Stock
            stocks = [str(p.stock) for p in products]
            max_stock = max(p.stock for p in products)
            stock_cells = [f"**{s}**" if p.stock == max_stock else s for p, s in zip(products, stocks)]
            lines.append("| Stock | " + " | ".join(stock_cells) + " |")

            # Category
            lines.append("| Category | " + " | ".join([p.category for p in products]) + " |")

            # Subcategory
            lines.append("| Subcategory | " + " | ".join([p.subcategory or "N/A" for p in products]) + " |")

            # Features (first 3)
            for i in range(3):
                feature_cells = []
                for p in products:
                    feats = json.loads(p.features) if p.features else []
                    feature_cells.append(feats[i] if i < len(feats) else "—")
                lines.append(f"| Feature {i+1} | " + " | ".join(feature_cells) + " |")

            # Condition tags
            condition_cells = []
            for p in products:
                tags = [t.strip() for t in (p.condition_tags or "").split(",") if t.strip()]
                condition_cells.append(", ".join(tags[:3]) if tags else "—")
            lines.append("| Best For | " + " | ".join(condition_cells) + " |")

            # Recommendation summary
            lines.append("\n### Recommendation:\n")
            best_value = min(products, key=lambda p: p.price / max(p.rating, 0.1))
            best_rated = max(products, key=lambda p: p.rating)
            lines.append(
                f"- **Best Value:** {best_value.name} (₹{best_value.price:,.2f}, {best_value.rating}/5)\n"
                f"- **Best Rated:** {best_rated.name} ({best_rated.rating}/5)\n"
            )

            return "\n".join(lines)

    except Exception as e:
        logger.error("Product comparison failed: %s", e)
        return f"Sorry, the comparison encountered an error. Please try again. (Error: {type(e).__name__})"
