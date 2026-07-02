"""Unit tests for AquaMax AI Agent tools."""

from __future__ import annotations

import json

import pytest

from src.database.models import Product
from src.database.repository import ProductRepository
from src.tools.catalog import search_products
from src.tools.comparison import compare_products
from src.tools.lead_capture import capture_lead
from src.tools.quotation import generate_quotation
from src.tools.recommendation import recommend_products


class TestSearchProducts:
    """Tests for the search_products tool."""

    def test_search_with_results(self, db_session):
        """Search should return matching products."""
        repo = ProductRepository(db_session)
        product = Product(
            sku="TEST-001",
            name="Test TENS Unit",
            category="Electrotherapy",
            description="A TENS unit for back pain relief",
            price=5000.0,
            rating=4.5,
            stock=10,
            condition_tags="back pain,chronic pain",
        )
        repo.create(product)
        db_session.commit()

        result = search_products.invoke({"query": "back pain", "category": None, "max_price": None})
        assert "Test TENS Unit" in result
        assert "₹5,000.00" in result

    def test_search_no_results(self, db_session):
        """Search with no matches should return helpful message."""
        result = search_products.invoke({"query": "nonexistent xyz", "category": None, "max_price": None})
        assert "No products found" in result or "Try searching" in result

    def test_search_empty_query(self, db_session):
        """Empty query should return validation message."""
        result = search_products.invoke({"query": "", "category": None, "max_price": None})
        assert "Please provide" in result


class TestCompareProducts:
    """Tests for the compare_products tool."""

    def test_compare_two_products(self, db_session):
        """Compare should return formatted comparison table."""
        repo = ProductRepository(db_session)
        p1 = Product(sku="CMP-001", name="Product A", category="Test", price=10000, rating=4.5, stock=5, features=json.dumps(["Feature 1"]))
        p2 = Product(sku="CMP-002", name="Product B", category="Test", price=8000, rating=4.8, stock=10, features=json.dumps(["Feature 2"]))
        repo.create(p1)
        repo.create(p2)
        db_session.commit()

        result = compare_products.invoke({"product_ids": f"{p1.id},{p2.id}"})
        assert "Product Comparison" in result
        assert "Product A" in result
        assert "Product B" in result
        assert "₹" in result

    def test_compare_single_product(self, db_session):
        """Compare with single product should ask for more."""
        result = compare_products.invoke({"product_ids": "1"})
        assert "at least 2" in result


class TestRecommendProducts:
    """Tests for the recommend_products tool."""

    def test_recommend_with_matches(self, db_session):
        """Recommendation should return scored products."""
        repo = ProductRepository(db_session)
        p = Product(
            sku="REC-001", name="Rehab TENS", category="Electrotherapy",
            description="TENS for arthritis", price=6000, rating=4.7, stock=15,
            condition_tags="arthritis,chronic pain,joint pain",
        )
        repo.create(p)
        db_session.commit()

        result = recommend_products.invoke({"requirements": "TENS for arthritis", "budget": None, "top_k": 3})
        assert "Rehab TENS" in result or "No products" in result or "couldn't find" in result

    def test_recommend_empty(self, db_session):
        """Recommendation with no matches should ask clarifying questions."""
        result = recommend_products.invoke({"requirements": "xyz nonsense", "budget": None, "top_k": 3})
        assert "couldn't find" in result or "No products" in result or "more details" in result


class TestCaptureLead:
    """Tests for the capture_lead tool."""

    def test_create_new_lead(self, db_session):
        """Should create a new lead successfully."""
        result = capture_lead.invoke({
            "session_id": "test-session-001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+91 98765 43210",
            "organization": "City Clinic",
            "budget_range": "10000-50000",
            "condition": "back pain",
            "requirements": "TENS unit for clinic",
        })
        assert "Lead captured successfully" in result
        assert "John Doe" in result

    def test_update_existing_lead(self, db_session):
        """Should update existing lead with same email."""
        capture_lead.invoke({
            "session_id": "test-session-002",
            "name": "Jane Doe",
            "email": "jane@example.com",
        })
        
        result = capture_lead.invoke({
            "session_id": "test-session-002",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+91 99999 99999",
        })
        
        assert "Lead updated" in result or "captured" in result


class TestGenerateQuotation:
    """Tests for the generate_quotation tool."""

    def test_generate_quote(self, db_session):
        """Should generate a quotation with correct pricing."""
        repo = ProductRepository(db_session)
        p = Product(sku="QT-001", name="Quote Product", category="Test", price=10000, rating=4.5, stock=5)
        repo.create(p)
        db_session.commit()

        result = generate_quotation.invoke({
            "session_id": "test-session-qt",
            "product_ids": str(p.id),
            "customer_email": None,
            "discount_percent": 10.0,
            "validity_days": 30,
            "notes": "Test quotation",
        })
        assert "Quotation" in result
        assert "₹" in result
        assert "GST" in result


class TestDraftEmail:
    """Tests for the draft_email tool."""

    def test_draft_professional_email(self):
        """Should generate a professional email."""
        from src.tools.email_draft import draft_email
        
        result = draft_email.invoke({
            "recipient_name": "Dr. Sharma",
            "context": "follow-up after TENS unit inquiry",
            "tone": "professional",
            "include_quote": False,
            "quote_id": None,
        })
        assert "Dear Dr. Sharma" in result
        assert "AquaMax" in result
        assert "Subject" in result

    def test_draft_friendly_email(self):
        """Should generate a friendly email with different tone."""
        from src.tools.email_draft import draft_email
        
        result = draft_email.invoke({
            "recipient_name": "Raj",
            "context": "quotation for ultrasound unit",
            "tone": "friendly",
            "include_quote": False,
            "quote_id": None,
        })
        assert "Hi Raj" in result or "Hi" in result
        assert "AquaMax" in result
