from src.tools.catalog import search_products
from src.tools.comparison import compare_products
from src.tools.email_draft import draft_email
from src.tools.lead_capture import capture_lead
from src.tools.quotation import generate_quotation
from src.tools.recommendation import recommend_products

ALL_TOOLS = [
    search_products,
    compare_products,
    recommend_products,
    capture_lead,
    generate_quotation,
    draft_email,
]

__all__ = [
    "ALL_TOOLS",
    "search_products",
    "compare_products",
    "recommend_products",
    "capture_lead",
    "generate_quotation",
    "draft_email",
]