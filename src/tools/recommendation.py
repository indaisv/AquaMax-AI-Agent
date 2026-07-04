"""Product recommendation engine tool."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repository import ProductRepository
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.database.models import Product

logger = get_logger(__name__)


@tool
def recommend_products(requirements: str, budget: str | None = None, top_k: int | str = 3) -> str:
    """Recommend the best rehabilitation equipment based on customer requirements and budget.

    Use this tool when the user describes their needs, condition, or clinic setup and wants product suggestions.
    The recommendation engine scores products by condition match, budget fit, rating, and stock availability.

    Args:
        requirements: Description of needs, condition, body part, or clinic type (e.g., "TENS for back pain in a physiotherapy clinic")
        budget: Optional budget range (e.g., "under 10000", "5000-15000", "no limit")
        top_k: Number of recommendations to return (default 3, max 5)
    """
    try:
        # Groq Llama3 sometimes passes top_k as a string; convert safely
        if isinstance(top_k, str):
            try:
                top_k = int(top_k)
            except ValueError:
                top_k = 3
        top_k = min(max(top_k, 1), 5)

        budget_max = None
        if budget:
            budget_lower = budget.lower()
            if "under" in budget_lower or "below" in budget_lower or "less than" in budget_lower:
                nums = re.findall(r"\d+", budget_lower)
                if nums:
                    budget_max = float(nums[0])
                    if "lakh" in budget_lower or "lac" in budget_lower:
                        budget_max *= 100000
                    elif "crore" in budget_lower:
                        budget_max *= 10000000
            elif "-" in budget:
                nums = re.findall(r"\d+", budget_lower)
                if len(nums) >= 2:
                    budget_max = float(nums[1])
                    if "lakh" in budget_lower or "lac" in budget_lower:
                        budget_max *= 100000

        with get_session() as session:
            repo = ProductRepository(session)
            
            # Split requirements into keywords for better matching
            keywords = [kw.strip() for kw in requirements.split() if len(kw.strip()) >= 2]
            if not keywords:
                keywords = [requirements]
            
            # Try keyword search first
            candidates: list[Product] = repo.search_by_keywords(keywords, max_price=budget_max)
            
            # Fallback to condition search with individual keywords
            if not candidates:
                for kw in keywords:
                    condition_results = repo.filter_by_condition(kw)
                    if condition_results:
                        candidates.extend(condition_results)
                # Deduplicate
                seen = set()
                candidates = [p for p in candidates if not (p.id in seen or seen.add(p.id))]
            
            # Final fallback: list all products
            if not candidates:
                candidates = repo.list_all(limit=20)

            scored = []
            for p in candidates:
                score = 0.0
                data = p.to_dict()
                score += (p.rating / 5.0) * 30
                score += min(p.stock / 100, 1.0) * 20
                req_lower = requirements.lower()
                tags = [t.lower() for t in data.get("condition_tags", [])]
                tag_matches = sum(1 for t in tags if any(word in t for word in req_lower.split()))
                score += min(tag_matches / 3, 1.0) * 30
                if budget_max:
                    if p.price <= budget_max:
                        score += (1 - (p.price / budget_max)) * 20
                else:
                    score += 10
                scored.append((score, p))

            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:top_k]

            if not top:
                return (
                    "I couldn't find any products matching your requirements.\n"
                    "Could you share more details? For example:\n"
                    "- What condition or body part? (e.g., back pain, knee rehab)\n"
                    "- What type of equipment? (e.g., TENS, ultrasound, walker)\n"
                    "- Your budget range?"
                )

            lines = [f"## Top {len(top)} Recommendations for: {requirements}\n"]
            for i, (score, p) in enumerate(top, 1):
                data = p.to_dict()
                features = ", ".join(data["features"][:3]) if data["features"] else ""
                tags = [t.strip() for t in (p.condition_tags or "").split(",") if t.strip()]
                relevant_tags = [t for t in tags if any(word in t.lower() for word in requirements.lower().split())]
                lines.append(
                    f"{i}. **{data['name']}** — ₹{data['price']:,.2f}\n"
                    f"   - **Match Score:** {score:.1f}/100 | **Rating:** {data['rating']}/5.0\n"
                    f"   - **Category:** {data['category']} | **Stock:** {data['stock']} units\n"
                    f"   - **Key Features:** {features}\n"
                    f"   - **Best For:** {', '.join(relevant_tags[:3]) or ', '.join(tags[:3])}\n"
                    f"   - {data['description'][:150]}...\n"
                )

            lines.append("\nWould you like me to compare these products, generate a quotation, or provide more details about any specific item?")
            return "\n".join(lines)

    except Exception as e:
        logger.error("Recommendation failed: %s", e)
        return f"Sorry, the recommendation engine encountered an error. Please try again. (Error: {type(e).__name__})"
