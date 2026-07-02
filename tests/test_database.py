"""Unit tests for database layer."""

from __future__ import annotations

import json

import pytest

from src.database.models import Conversation, Lead, Product, Quotation
from src.database.repository import (
    ConversationRepository,
    LeadRepository,
    ProductRepository,
    QuotationRepository,
)


class TestProductRepository:
    """Tests for ProductRepository."""

    def test_create_and_get(self, db_session):
        """Should create and retrieve a product."""
        repo = ProductRepository(db_session)
        product = Product(
            sku="DB-001",
            name="DB Test Product",
            category="Test",
            price=9999.0,
            rating=4.5,
            stock=20,
        )
        repo.create(product)
        db_session.commit()

        fetched = repo.get_by_id(product.id)
        assert fetched is not None
        assert fetched.name == "DB Test Product"
        assert fetched.sku == "DB-001"

    def test_search(self, db_session):
        """Should search products by query."""
        repo = ProductRepository(db_session)
        repo.create(Product(sku="S-001", name="Searchable Item", category="Test", description="For back pain", price=1000, rating=4.0, stock=5))
        db_session.commit()

        results = repo.search("back pain")
        assert len(results) >= 1
        assert any(p.name == "Searchable Item" for p in results)

    def test_filter_by_condition(self, db_session):
        """Should filter products by condition tags."""
        repo = ProductRepository(db_session)
        repo.create(Product(sku="C-001", name="Condition Product", category="Test", price=1000, rating=4.0, stock=5, condition_tags="arthritis,back pain"))
        db_session.commit()

        results = repo.filter_by_condition("arthritis")
        assert len(results) >= 1

    def test_count(self, db_session):
        """Should return correct product count."""
        repo = ProductRepository(db_session)
        initial = repo.count()
        repo.create(Product(sku="CNT-001", name="Count Product", category="Test", price=1000, rating=4.0, stock=5))
        db_session.commit()
        assert repo.count() == initial + 1


class TestLeadRepository:
    """Tests for LeadRepository."""

    def test_create_and_get_by_email(self, db_session):
        """Should create and retrieve lead by email."""
        repo = LeadRepository(db_session)
        lead = Lead(session_id="lead-test-001", name="Test Lead", email="test@example.com", status="new")
        repo.create(lead)
        db_session.commit()

        fetched = repo.get_by_email("test@example.com")
        assert fetched is not None
        assert fetched.name == "Test Lead"

    def test_get_by_session(self, db_session):
        """Should retrieve lead by session ID."""
        repo = LeadRepository(db_session)
        lead = Lead(session_id="sess-123", name="Session Lead", email="sess@example.com")
        repo.create(lead)
        db_session.commit()

        fetched = repo.get_by_session("sess-123")
        assert fetched is not None
        assert fetched.name == "Session Lead"

    def test_update(self, db_session):
        """Should update lead information."""
        repo = LeadRepository(db_session)
        lead = Lead(session_id="upd-001", name="Old Name", email="upd@example.com")
        repo.create(lead)
        db_session.commit()

        lead.name = "New Name"
        repo.update(lead)
        db_session.commit()

        fetched = repo.get_by_email("upd@example.com")
        assert fetched.name == "New Name"


class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_create_and_get_by_session(self, db_session):
        """Should persist and retrieve conversation history."""
        repo = ConversationRepository(db_session)
        repo.create(Conversation(session_id="conv-001", role="user", content="Hello"))
        repo.create(Conversation(session_id="conv-001", role="assistant", content="Hi there!"))
        db_session.commit()

        history = repo.get_by_session("conv-001")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_delete_by_session(self, db_session):
        """Should delete all messages for a session."""
        repo = ConversationRepository(db_session)
        repo.create(Conversation(session_id="del-001", role="user", content="Test"))
        db_session.commit()

        deleted = repo.delete_by_session("del-001")
        assert deleted == 1
        db_session.commit()

        history = repo.get_by_session("del-001")
        assert len(history) == 0


class TestQuotationRepository:
    """Tests for QuotationRepository."""

    def test_create_and_get(self, db_session):
        """Should create and retrieve a quotation."""
        repo = QuotationRepository(db_session)
        quotation = Quotation(
            session_id="qt-001",
            products=json.dumps([{"id": 1, "name": "Test Product", "price": 5000}]),
            subtotal=5000.0,
            total=5900.0,
            status="draft",
        )
        repo.create(quotation)
        db_session.commit()

        fetched = repo.get_by_id(quotation.id)
        assert fetched is not None
        assert fetched.total == 5900.0

    def test_get_by_session(self, db_session):
        """Should retrieve quotations by session."""
        repo = QuotationRepository(db_session)
        repo.create(Quotation(session_id="qt-sess", subtotal=1000, total=1180, status="draft"))
        db_session.commit()

        results = repo.get_by_session("qt-sess")
        assert len(results) == 1


class TestProductModel:
    """Tests for Product model serialization."""

    def test_to_dict(self, db_session):
        """Should serialize product to dictionary."""
        product = Product(
            sku="MD-001",
            name="Model Product",
            category="Test",
            price=1000,
            rating=4.0,
            stock=5,
            features=json.dumps(["F1", "F2"]),
            condition_tags="tag1,tag2",
        )
        data = product.to_dict()
        assert data["name"] == "Model Product"
        assert data["price"] == 1000
        assert data["features"] == ["F1", "F2"]
        assert data["condition_tags"] == ["tag1", "tag2"]
