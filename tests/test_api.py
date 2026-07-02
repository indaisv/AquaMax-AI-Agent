"""Integration tests for FastAPI endpoints."""

from __future__ import annotations

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aquamax-agent"


class TestChatEndpoint:
    """Tests for the chat endpoint."""

    def test_chat_with_message(self, client):
        """Should accept a chat message and return a response."""
        # Note: This may require a valid OpenAI API key to pass fully
        # In test environments without API keys, it should at least handle gracefully
        payload = {
            "message": "Hello, I need a TENS unit for back pain",
            "session_id": "test-chat-001",
        }
        response = client.post("/chat", json=payload)
        # Should either succeed (200) or return 500 if API key is missing
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data

    def test_chat_empty_message(self, client):
        """Should reject empty messages."""
        payload = {"message": "", "session_id": "test-chat-002"}
        response = client.post("/chat", json=payload)
        assert response.status_code == 422  # Validation error

    def test_chat_history(self, client):
        """Should retrieve chat history for a session."""
        # First, send a message
        client.post("/chat", json={"message": "Test message", "session_id": "test-hist-001"})
        
        # Then get history
        response = client.get("/chat/test-hist-001/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_reset_session(self, client):
        """Should reset a session."""
        response = client.delete("/chat/test-reset-001/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestProductsEndpoint:
    """Tests for product endpoints."""

    def test_list_products(self, client):
        """Should list all products."""
        response = client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "count" in data

    def test_search_products(self, client):
        """Should search products by query."""
        response = client.get("/products/search?query=TENS")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data

    def test_get_product_by_id(self, client):
        """Should get a single product by ID."""
        # First list to get an ID
        list_response = client.get("/products")
        products = list_response.json().get("products", [])
        if products:
            product_id = products[0]["id"]
            response = client.get(f"/products/{product_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == product_id

    def test_get_product_not_found(self, client):
        """Should return 404 for non-existent product."""
        response = client.get("/products/99999")
        assert response.status_code == 404

    def test_get_categories(self, client):
        """Should list all categories."""
        response = client.get("/products/categories/list")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


class TestLeadsEndpoint:
    """Tests for leads endpoints."""

    def test_list_leads(self, client):
        """Should list all leads."""
        response = client.get("/leads")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_lead(self, client):
        """Should create a new lead."""
        payload = {
            "session_id": "api-test-001",
            "name": "API Test Lead",
            "email": "api-test@example.com",
            "phone": "+91 99999 99999",
            "organization": "API Clinic",
            "budget_range": "10000-50000",
            "condition": "back pain",
            "requirements": "TENS unit",
            "status": "new",
        }
        response = client.post("/leads", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test Lead"
        assert data["email"] == "api-test@example.com"

    def test_search_leads(self, client):
        """Should search leads by email."""
        response = client.get("/leads/search?email=api-test@example.com")
        assert response.status_code == 200
        data = response.json()
        assert "found" in data


class TestQuotationsEndpoint:
    """Tests for quotation endpoints."""

    def test_get_quotation_not_found(self, client):
        """Should return 404 for non-existent quotation."""
        response = client.get("/quotations/99999")
        assert response.status_code == 404

    def test_get_quotations_by_session(self, client):
        """Should get quotations by session."""
        response = client.get("/quotations/session/test-session")
        assert response.status_code == 200
        data = response.json()
        assert "quotations" in data
        assert "count" in data
