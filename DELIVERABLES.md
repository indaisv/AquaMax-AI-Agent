# Deliverables — AquaMax AI Agent

> This document contains all career-ready materials generated alongside the project.

---

## 1. Resume Bullet Points

### AI Automation Engineer / AI Engineer / ML Engineer Resume Bullets

**Project Title:** AquaMax AI Sales & Support Agent — Production-Ready AI Agent

**Bullets (choose 3-5 for your resume):**

1. **Built a production-grade AI Sales & Support Agent** using LangGraph state-machine graphs, LangChain tool calling, and OpenAI-compatible LLMs — automating product search, recommendations, quotations, and lead capture for a rehabilitation equipment company.

2. **Architected a modular agent system** with 6 specialized tools (search, compare, recommend, capture lead, generate quotation, draft email) using clean architecture principles — SOLID, DRY, repository pattern, and dependency injection.

3. **Developed a FastAPI backend** with async endpoints, Pydantic v2 validation, auto-generated OpenAPI docs, and structured error handling — serving as the REST API layer for the AI agent.

4. **Implemented conversation memory and session management** using SQLite-backed persistence with SQLAlchemy ORM — enabling multi-turn dialogues with context retention across customer interactions.

5. **Designed a conditional-routing LangGraph workflow** with intent classification, entity extraction, and graceful error recovery — handling edge cases like ambiguous queries, missing info, and API failures.

6. **Built a Streamlit frontend** with chat interface, product catalog browser, leads dashboard, and session management — demonstrating full-stack AI agent delivery from backend to UI.

7. **Wrote comprehensive test suite** with pytest including unit tests for tools, database layer tests, and FastAPI integration tests — achieving test coverage for core business logic.

8. **Deployed sample catalog of 30+ products** with fuzzy search, condition-based filtering, and AI-powered scoring — enabling intelligent product recommendations based on medical conditions and budget.

---

## 2. LinkedIn Project Description

### Headline (for Featured Section)
> **AquaMax AI Sales & Support Agent** — Intelligent AI Agent for Rehabilitation Equipment

### Description (copy-paste ready)

```
Built a production-ready AI Sales & Support Agent for AquaMax Rehab Equipment using 
LangGraph, LangChain, FastAPI, and Streamlit. 

The agent autonomously handles:
🔍 Product search & catalog browsing
⭐ Intelligent recommendations based on condition & budget
📊 Side-by-side product comparisons
📝 Automatic lead capture & CRM integration
💰 Quotation generation with GST & terms
📧 Professional follow-up email drafting
🧠 Multi-turn conversation memory

Tech Stack: Python · LangGraph · LangChain · OpenAI API · FastAPI · Streamlit · SQLite · SQLAlchemy · Pydantic · pytest

Architecture: Clean Architecture · State-machine graphs · Tool calling · Repository pattern · Dependency injection

Key Features:
• 6 AI-powered tools with automatic function calling
• Conditional routing based on intent classification
• Graceful error handling with human handoff
• Full REST API with auto-generated docs
• Interactive chat UI with admin dashboard
• Comprehensive test suite (unit + integration)

This project demonstrates end-to-end AI agent engineering — from LLM orchestration 
to production API design to user-facing interfaces.

#AI #MachineLearning #GenAI #LangChain #FastAPI #Python #AIAgent #LLM #DataScience
```

### LinkedIn Post (to announce the project)

```
🚀 Just shipped a production-ready AI Agent!

I built the AquaMax AI Sales & Support Agent — an intelligent assistant that helps 
customers find the right rehabilitation equipment through natural conversation.

What it does:
→ Understands customer needs via intent classification
→ Searches & recommends 30+ products from the catalog
→ Compares products side-by-side
→ Captures leads automatically into a database
→ Generates quotations with GST, discounts, and terms
→ Drafts professional follow-up emails
→ Remembers conversation context across multiple turns

Built with:
🧠 LangGraph — state-machine agent graphs
🔗 LangChain — LLM tool orchestration
⚡ FastAPI — async REST API
🎨 Streamlit — chat UI & dashboards
🗄️ SQLite + SQLAlchemy — data persistence
✅ pytest — unit & integration tests

Why this matters: This isn't a chatbot. It's an AI agent that uses tools, 
maintains memory, handles errors gracefully, and delivers real business value.

Check it out on GitHub 👇
[Link to repo]

#AI #GenAI #LangChain #FastAPI #Python #MachineLearning #LLM #AIEngineer #BuildingInPublic
```

---

## 3. Interview Questions & Answers

### Q1: What is the difference between a chatbot and an AI agent?

**A:** A chatbot is typically a reactive system that maps user inputs to pre-defined responses. An AI agent, like the one I built, is proactive — it can reason about goals, plan multi-step actions, use tools (function calling), maintain state across interactions, and handle errors autonomously. In this project, the agent doesn't just answer questions; it searches a database, compares products, generates quotations, and captures leads — all by deciding which tools to use based on the conversation context.

---

### Q2: Why did you choose LangGraph over a simple LangChain chain?

**A:** LangGraph provides a state-machine graph structure that's essential for complex agent behavior. With simple chains, the flow is linear — you can't loop back to ask clarifying questions or branch based on intent. LangGraph gives me:
- **Conditional routing**: Different intents → different processing paths
- **Cycles**: The agent can ask follow-up questions and re-process
- **Persistence**: Built-in checkpointing for conversation memory
- **Observability**: Each node is independently testable and debuggable

In this project, I have 10 nodes (classify_intent, extract_entities, search_catalog, compare_products, recommend, capture_lead, generate_quote, draft_email, build_response, error_handler) with conditional edges between them.

---

### Q3: How does your agent handle errors gracefully?

**A:** I implemented a three-layer error handling strategy:
1. **Tool-level**: Every tool has try/except with safe fallbacks. If search fails, it returns a helpful message instead of crashing.
2. **Node-level**: Each graph node is wrapped so exceptions set an error flag and route to the error_handler node.
3. **Graph-level**: Unrecoverable errors set `requires_human = True` and provide a recovery message.

In the API layer, FastAPI exception handlers catch AquaMaxError subclasses and return structured JSON errors. The UI shows error banners with retry options.

---

### Q4: Explain your Clean Architecture approach.

**A:** I organized the codebase into 5 layers with clear dependencies:
- **UI Layer** (Streamlit): Only talks to the API layer
- **API Layer** (FastAPI routers): Handles HTTP, validation, and routing to services
- **Service Layer** (AquaMaxAgent, CustomerService, ProductService): Business logic orchestration
- **Tool Layer** (6 tools): Single-responsibility functions that the agent calls
- **Data Layer** (SQLAlchemy ORM + Repository pattern): Database access abstracted behind interfaces

This follows SOLID principles: each tool has one responsibility (SRP), repositories are swappable (DIP), and the graph is composed of independent nodes that can be tested in isolation.

---

### Q5: How does the recommendation engine work?

**A:** The recommendation engine is a hybrid scoring system that combines rule-based heuristics with LLM reasoning. It scores products across four dimensions:
- **Rating score** (0-30): Higher-rated products score better
- **Stock score** (0-20): Well-stocked products are preferred
- **Condition match** (0-30): Products matching the user's medical condition get higher scores
- **Budget fit** (0-20): Products within budget range; if no budget is specified, it scores neutrally

The top-k products are returned with explanations. This approach is fast (no LLM call needed for scoring), interpretable, and can be easily extended with vector similarity or collaborative filtering.

---

### Q6: How did you handle conversation memory?

**A:** I implemented a two-tier memory system:
1. **LangGraph state**: The `messages` field in AgentState is an `Annotated[list, add_messages]` that accumulates messages within a single graph invocation.
2. **SQLite persistence**: A `ConversationMemory` class persists every message to the database with session_id. When a user returns, their history is loaded into the context window.

This ensures the agent remembers previous turns, customer information, and tool results across a conversation session. For production, I'd add Redis for fast retrieval and a summarization strategy for very long conversations.

---

### Q7: What would you change for a production deployment at scale?

**A:** Several things:
1. **Vector DB**: Replace fuzzy search with Pinecone/Weaviate for semantic product search (RAG)
2. **Database**: Move from SQLite to PostgreSQL for concurrent access and replication
3. **Caching**: Add Redis for conversation state and frequent queries
4. **Async**: Make tool calls async to avoid blocking the event loop
5. **Authentication**: OAuth2/JWT for sales rep accounts and API access control
6. **Monitoring**: Add Prometheus metrics, structured logging, and APM tracing
7. **CI/CD**: GitHub Actions for automated testing and deployment
8. **Human handoff**: WebSocket integration for real-time human takeover when needed

---

### Q8: How do you test an AI agent?

**A:** I use a multi-layered testing strategy:
- **Unit tests**: Each tool is tested independently with in-memory SQLite, mocking the database layer
- **Integration tests**: FastAPI endpoints are tested with TestClient, verifying the full request/response cycle
- **Database tests**: Repository pattern makes it easy to test CRUD operations with a fresh in-memory DB per test
- **Mock LLM**: For testing the graph logic without API calls, I'd mock the LLM responses (though I used real integration for the actual project)

The key is isolating the tool layer from the LLM layer so business logic can be tested without API keys.

---

### Q9: What was the hardest technical challenge?

**A:** The hardest challenge was designing the conditional routing in the LangGraph so that the agent could handle ambiguous user inputs gracefully. For example, if someone says "I need something for my clinic," the intent classifier returns "general" or "recommend," but the agent needs to ask clarifying questions instead of guessing.

I solved this by adding an `extract_entities` node that pulls out whatever information IS available, and a `clarification_needed` flag in the state. If critical info (like condition or budget) is missing, the response builder generates a clarifying question rather than making a blind recommendation.

---

### Q10: How does this project demonstrate your fit for an AI Automation Engineer role?

**A:** This project directly addresses the core responsibilities of an AI Automation Engineer:
- **LLM orchestration**: I designed and implemented a multi-node agent graph with conditional routing
- **Tool integration**: I built 6 real tools that interact with a database and return structured data
- **API development**: I created a production-ready FastAPI backend with proper validation and error handling
- **Full-stack delivery**: I built both the backend and a user-facing Streamlit UI
- **Data layer**: I implemented SQLAlchemy ORM with repository pattern for clean data access
- **Testing**: I wrote comprehensive tests covering tools, database, and API layers
- **Production thinking**: I included logging, environment configuration, graceful degradation, and deployment documentation

This isn't a toy project — it's a complete business automation system that could be deployed to help real customers.

---

## 4. GitHub Repository Description

```
# AquaMax AI Sales & Support Agent

A production-ready AI agent built for AquaMax Rehab Equipment that automates 
sales assistance and customer support through intelligent conversation.

## 🎯 What It Does
- 🔍 Searches and recommends rehabilitation equipment
- 📊 Compares products side-by-side  
- 📝 Captures customer leads automatically
- 💰 Generates quotations with pricing and terms
- 📧 Drafts professional follow-up emails
- 🧠 Remembers conversation context across turns

## 🛠️ Tech Stack
LangGraph · LangChain · OpenAI API · FastAPI · Streamlit · SQLite · SQLAlchemy · Pydantic · pytest

## 🚀 Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY
python -m src.database.seed
uvicorn api.main:app --reload
# In another terminal: streamlit run ui/app.py
```

## 📊 Architecture
```
Streamlit UI → FastAPI → LangGraph Agent → Tools → SQLite
                      ↓
                OpenAI LLM
```

Built by [Viraj Indais](https://linkedin.com/in/viraj-indais) — AI Automation Engineer
```

---

## 5. Future Improvements Roadmap

### Phase 1: Enhanced Search (2-3 weeks)
- [ ] Vector DB integration (Pinecone/Weaviate) for semantic search
- [ ] Product image understanding with vision models
- [ ] Multi-modal queries ("show me equipment for knee pain under 10k")

### Phase 2: Scale & Performance (2-3 weeks)
- [ ] PostgreSQL migration with connection pooling
- [ ] Redis caching for product catalog and sessions
- [ ] Async tool calls with asyncio
- [ ] Rate limiting and API key management

### Phase 3: Enterprise Features (3-4 weeks)
- [ ] OAuth2/JWT authentication for sales reps
- [ ] Role-based access control (admin, sales, viewer)
- [ ] Multi-tenant support for multiple equipment vendors
- [ ] Audit logs and compliance reporting

### Phase 4: Advanced AI (4-6 weeks)
- [ ] Voice interface (Whisper + TTS)
- [ ] Real-time human handoff via WebSocket
- [ ] A/B testing framework for recommendation algorithms
- [ ] Reinforcement learning from human feedback (RLHF)

### Phase 5: Analytics & Ops (2-3 weeks)
- [ ] Power BI dashboard for lead conversion metrics
- [ ] Prometheus + Grafana monitoring
- [ ] Automated email campaigns based on lead status
- [ ] ERP integration for live inventory and pricing
