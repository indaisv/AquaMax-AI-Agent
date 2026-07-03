"""Quotation generation tool."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.models import Quotation
from src.database.repository import LeadRepository, ProductRepository, QuotationRepository
from src.utils.helpers import format_currency
from src.utils.logger import get_logger

logger = get_logger(__name__)


@tool
def generate_quotation(
    session_id: str,
    product_ids: str,
    customer_email: str | None = None,
    discount_percent: float | str = 0.0,
    validity_days: int | str = 30,
    notes: str | None = None,
) -> str:
    """Generate a formal quotation for selected products.

    Use this tool when the customer wants a price quote, is ready to purchase, or asks for pricing details.

    Args:
        session_id: The conversation session ID
        product_ids: Comma-separated product IDs (e.g., "1,2")
        customer_email: Customer email for associating with lead
        discount_percent: Optional discount percentage (0-100)
        validity_days: Quote validity in days (default 30)
        notes: Additional notes or terms
    """
    try:
        # Groq Llama3 sometimes passes numeric params as strings; convert safely
        if isinstance(discount_percent, str):
            try:
                discount_percent = float(discount_percent)
            except ValueError:
                discount_percent = 0.0
        if isinstance(validity_days, str):
            try:
                validity_days = int(validity_days)
            except ValueError:
                validity_days = 30

        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip().isdigit()]
        if not ids:
            return "Please provide at least one product ID for the quotation."

        with get_session() as session:
            product_repo = ProductRepository(session)
            lead_repo = LeadRepository(session)
            quote_repo = QuotationRepository(session)

            products = product_repo.get_by_ids(ids)
            if not products:
                return f"No products found with IDs: {product_ids}. Please check the product IDs."

            subtotal = sum(p.price for p in products)
            discount = subtotal * (discount_percent / 100.0)
            tax = (subtotal - discount) * 0.18
            total = subtotal - discount + tax

            lead_id = None
            if customer_email:
                lead = lead_repo.get_by_email(customer_email)
                if lead:
                    lead_id = lead.id
            if not lead_id:
                lead = lead_repo.get_by_session(session_id)
                if lead:
                    lead_id = lead.id

            product_list = []
            for p in products:
                product_list.append({
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "price": p.price,
                    "quantity": 1,
                })

            quotation = Quotation(
                session_id=session_id,
                lead_id=lead_id,
                products=json.dumps(product_list),
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                validity_days=validity_days,
                terms=(
                    "1. Prices valid for the specified validity period.\n"
                    "2. GST included at 18%.\n"
                    "3. Delivery within 7-14 business days.\n"
                    "4. Warranty as per manufacturer terms.\n"
                    "5. Payment: 50% advance, 50% on delivery."
                ),
                notes=notes or "",
                status="draft",
            )
            quote_repo.create(quotation)

            lines = [
                "## AquaMax Rehab Equipment — Quotation",
                f"**Quotation ID:** QT-{quotation.id:06d}",
                f"**Valid Until:** {validity_days} days from issue",
                f"**Status:** Draft\n",
                "### Products:",
            ]
            for p in products:
                lines.append(f"- {p.name} (SKU: {p.sku}) — {format_currency(p.price)}")

            lines.extend(["", f"**Subtotal:** {format_currency(subtotal)}"])
            if discount > 0:
                lines.append(f"**Discount ({discount_percent}%):** -{format_currency(discount)}")
            lines.extend([
                f"**GST (18%):** {format_currency(tax)}",
                f"**Total:** {format_currency(total)}",
                "",
                "### Terms & Conditions:",
                quotation.terms,
            ])
            if notes:
                lines.extend(["", f"**Notes:** {notes}"])

            lines.append(
                f"\nThis quotation has been saved (ID: {quotation.id}). "
                "Would you like me to draft a follow-up email with this quotation?"
            )

            return "\n".join(lines)

    except Exception as e:
        logger.error("Quotation generation failed: %s", e)
        return f"Sorry, the quotation generation encountered an error. Please try again. (Error: {type(e).__name__})"
