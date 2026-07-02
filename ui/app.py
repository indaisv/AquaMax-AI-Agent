"""Streamlit UI for the AquaMax AI Sales & Support Agent.

Run with: streamlit run ui/app.py
"""

from __future__ import annotations

import random
import uuid
from typing import Any

import requests
import streamlit as st

# ───────────────────────────────────────────────────────────────
# Page Configuration
# ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AquaMax AI Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

SAMPLE_PROMPTS = [
    "I need a TENS unit for chronic back pain",
    "What equipment do you recommend for a physiotherapy clinic?",
    "Compare the TENS Unit Pro and the EMS Muscle Stimulator",
    "I need a wheelchair for my elderly father",
    "What's the price of the underwater treadmill?",
    "Can you recommend something for knee rehabilitation after ACL surgery?",
    "I want to set up a home care setup for my mother who's bedridden",
    "Generate a quotation for the massage table and massage gun",
    "Draft a follow-up email for my inquiry about the parallel bars",
]

# ───────────────────────────────────────────────────────────────
# Session State Initialization
# ───────────────────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False


# ───────────────────────────────────────────────────────────────
# Helper Functions
# ───────────────────────────────────────────────────────────────

def check_api_health() -> bool:
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def send_chat_message(message: str) -> dict[str, Any] | None:
    """Send a message to the chat API and return the response."""
    try:
        payload = {
            "message": message,
            "session_id": st.session_state.session_id,
        }
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def fetch_products(category: str | None = None) -> list[dict]:
    """Fetch products from the API."""
    try:
        params = {}
        if category and category != "All":
            params["category"] = category
        response = requests.get(f"{API_BASE_URL}/products", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])
    except Exception:
        return []


def fetch_leads() -> list[dict]:
    """Fetch all leads from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/leads", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def fetch_categories() -> list[str]:
    """Fetch product categories from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/products/categories/list", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("categories", [])
    except Exception:
        return []


# ───────────────────────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🏥 AquaMax AI")
    st.markdown("*Intelligent Sales & Support Agent*")
    st.divider()

    # API Status
    st.subheader("API Status")
    if check_api_health():
        st.success("✅ Backend Connected")
        st.session_state.api_connected = True
    else:
        st.error("❌ Backend Offline")
        st.session_state.api_connected = False
        st.info("Start the backend with:\n```\npython -m uvicorn api.main:app --reload\n```")

    st.divider()

    # Navigation
    st.subheader("Navigation")
    page = st.radio(
        "Go to:",
        ["💬 Chat", "📋 Product Catalog", "👥 Leads Dashboard", "📄 About"],
    )

    st.divider()

    # Session Management
    st.subheader("Session")
    st.code(st.session_state.session_id[:8], language="text")
    if st.button("🔄 New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("---")
    st.caption("Built with LangGraph · FastAPI · Streamlit")


# ───────────────────────────────────────────────────────────────
# Chat Page
# ───────────────────────────────────────────────────────────────

if page == "💬 Chat":
    st.title("💬 AquaMax AI Assistant")
    st.markdown("Ask about rehabilitation equipment, get recommendations, compare products, or request a quotation.")

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("What are you looking for?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.api_connected:
                    result = send_chat_message(prompt)
                    if result:
                        response_text = result.get("response", "No response")
                        
                        # Show tool usage if any
                        tools_used = result.get("tools_used", [])
                        if tools_used:
                            st.caption(f"🔧 Tools used: {', '.join(tools_used)}")
                        
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    else:
                        st.error("Failed to get response from the AI agent.")
                else:
                    st.warning("Backend is offline. Please start the FastAPI server.")

    # Sample prompts
    if not st.session_state.messages:
        st.divider()
        st.subheader("💡 Try asking:")
        cols = st.columns(2)
        for i, sample in enumerate(SAMPLE_PROMPTS[:6]):
            with cols[i % 2]:
                if st.button(sample, key=f"sample_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": sample})
                    st.rerun()


# ───────────────────────────────────────────────────────────────
# Product Catalog Page
# ───────────────────────────────────────────────────────────────

elif page == "📋 Product Catalog":
    st.title("📋 Product Catalog")
    
    categories = ["All"] + fetch_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    search_query = st.text_input("Search products", placeholder="e.g., TENS, wheelchair, ultrasound...")
    
    products = fetch_products(category=selected_category if selected_category != "All" else None)
    
    if search_query:
        products = [p for p in products if search_query.lower() in p.get("name", "").lower() or search_query.lower() in p.get("description", "").lower()]
    
    st.write(f"Showing {len(products)} products")
    
    for product in products:
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.subheader(product.get("name", "Unnamed"))
                st.caption(f"{product.get('category', '')} | {product.get('subcategory', '')}")
                st.write(product.get("description", "")[:150] + "...")
                features = product.get("features", {})
                if isinstance(features, dict) and features:
                    st.write(", ".join([f"✓ {k}" for k in list(features.keys())[:3]]))
            with cols[1]:
                st.metric("Price", f"₹{product.get('price', 0):,.2f}")
                st.write(f"⭐ {product.get('rating', 0)}/5.0")
                st.write(f"📦 Stock: {product.get('stock', 0)}")
                st.write(f"SKU: {product.get('sku', '')}")


# ───────────────────────────────────────────────────────────────
# Leads Dashboard Page
# ───────────────────────────────────────────────────────────────

elif page == "👥 Leads Dashboard":
    st.title("👥 Leads Dashboard")
    st.markdown("View all captured customer leads from agent conversations.")
    
    leads = fetch_leads()
    
    if not leads:
        st.info("No leads captured yet. Start a chat conversation to capture leads.")
    else:
        st.write(f"Total leads: {len(leads)}")
        
        for lead in leads:
            with st.container(border=True):
                cols = st.columns([2, 2, 1])
                with cols[0]:
                    st.subheader(lead.get("name") or "Unnamed Lead")
                    st.write(f"📧 {lead.get('email') or 'No email'}")
                    st.write(f"📱 {lead.get('phone') or 'No phone'}")
                with cols[1]:
                    st.write(f"🏢 {lead.get('organization') or 'No organization'}")
                    st.write(f"💰 Budget: {lead.get('budget_range') or 'Not specified'}")
                    st.write(f"🏥 Condition: {lead.get('condition') or 'Not specified'}")
                with cols[2]:
                    st.write(f"Status: {lead.get('status', 'new')}")
                    st.write(f"ID: {lead.get('id')}")
                    st.write(f"Session: {lead.get('session_id', '')[:8]}...")


# ───────────────────────────────────────────────────────────────
# About Page
# ───────────────────────────────────────────────────────────────

elif page == "📄 About":
    st.title("📄 About AquaMax AI Agent")
    
    st.markdown("""
    ## 🏥 AquaMax Rehab Equipment — AI Sales & Support Agent
    
    This is a **production-ready AI Agent** built for AquaMax Rehab Equipment, a rehabilitation 
    and physiotherapy equipment company. It demonstrates enterprise-grade AI agent engineering 
    using modern Python, LangGraph, and FastAPI.
    
    ### Capabilities
    
    | Feature | Description |
    |---------|-------------|
    | 🔍 **Product Search** | Fuzzy search across 30+ rehab equipment products |
    | 📊 **Product Comparison** | Side-by-side comparison with highlighted differences |
    | ⭐ **Recommendations** | AI-powered recommendations based on condition & budget |
    | 📝 **Lead Capture** | Automatically saves customer information to SQLite |
    | 💰 **Quotation Generation** | Structured quotes with GST, discounts, and terms |
    | 📧 **Email Drafting** | Professional follow-up emails in multiple tones |
    | 🧠 **Conversation Memory** | Remembers context across multi-turn sessions |
    | 🔧 **Tool Calling** | Uses 6 specialized tools automatically |
    | ⚠️ **Error Handling** | Graceful degradation with human handoff |
    
    ### Tech Stack
    
    - **Agent Framework:** LangGraph (state-machine graph)
    - **LLM Integration:** LangChain + OpenAI-compatible API
    - **Backend API:** FastAPI (async, Pydantic, auto-docs)
    - **Frontend:** Streamlit (chat UI, dashboards)
    - **Database:** SQLite (SQLAlchemy ORM, repository pattern)
    - **Data Processing:** Pandas
    - **Testing:** pytest + pytest-asyncio
    - **Architecture:** Clean Architecture, SOLID, DRY
    
    ### Architecture
    
    ```
    Streamlit UI → FastAPI → LangGraph Agent → Tools → SQLite
                           ↓
                     OpenAI LLM
    ```
    
    ### Author
    
    **Viraj Indais** — AI Automation Engineer | Data Scientist
    - [LinkedIn](https://linkedin.com/in/viraj-indais)
    - [GitHub](https://github.com/viraj-indais)
    - [Email](mailto:indaisviraj@gmail.com)
    
    ---
    *Built for portfolio and educational purposes. MIT License.*
    """)
