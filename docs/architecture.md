# AquaMax AI Sales & Support Agent — Architecture Design

## 1. Overview

Production-ready AI Agent for **AquaMax Rehab Equipment** that acts as an intelligent sales assistant and customer support representative. It understands customer requirements, searches a product catalog, recommends products, compares options, generates quotations, captures leads, and drafts follow-up emails — all through natural conversation.

---

## 2. Architecture Decisions

### 2.1 Why LangGraph?
LangGraph provides a **state-machine graph** for agent workflows, which is superior to simple chains for multi-step reasoning:
- **Conditional routing**: Different user intents → different processing paths
- **Cycles/loops**: Can ask clarifying questions and re-process
- **Persistence**: Built-in checkpointing for conversation memory
- **Observability**: Each node is inspectable, debuggable, and testable

### 2.2 Why SQLite?
- Zero external dependency setup (fresher-friendly, no Docker/PostgreSQL needed)
- Sufficient for demo/catalog workloads
- File-based means easy backup, version control, and portability
- Can be swapped to PostgreSQL with a single repository change

### 2.3 Why FastAPI + Streamlit?
- **FastAPI**: Industry-standard Python async API framework. Demonstrates API design skills.
- **Streamlit**: Rapid UI prototyping. Shows full-stack capability without React complexity.
- Separation lets interviewers see backend architecture (API docs, REST design) and frontend UX.

### 2.4 Why Tool Calling (Function Calling)?
- Separates **reasoning** (LLM) from **action** (tools)
- Tools are unit-testable, mockable, and reusable
- Demonstrates understanding of modern AI agent patterns (ReAct, Toolformer)
- Each tool has a single responsibility (SRP)

### 2.5 Clean Architecture Layers
```
┌─────────────────────────────────────────────────────────┐
│  UI Layer          (Streamlit app.py)                   │
├─────────────────────────────────────────────────────────┤
│  API Layer         (FastAPI routers)                    │
├─────────────────────────────────────────────────────────┤
│  Service Layer     (Agent orchestration, business logic)│
├─────────────────────────────────────────────────────────┤
│  Tool Layer        (Search, Compare, Recommend, etc.)  │
├─────────────────────────────────────────────────────────┤
│  Data Layer        (SQLite repository, models)          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. State Graph Design (LangGraph)

### State Schema
```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # Conversation
    session_id: str                                     # Thread ID
    customer_info: dict                                 # Captured info
    intent: str                                         # Classified intent
    extracted_entities: dict                            # Parsed requirements
    search_results: list[Product]                         # Catalog matches
    comparison_data: dict                               # Comparison output
    recommendation: dict                                # Recommendation output
    quotation: dict                                     # Quote details
    email_draft: str                                    # Follow-up email
    error: str | None                                   # Error flag
    requires_human: bool                                # Handoff flag
    next_node: str                                      # Routing hint
```

### Nodes (10 total)
| # | Node | Purpose | Tool |
|---|------|---------|------|
| 1 | `classify_intent` | Understand user goal | LLM |
| 2 | `extract_entities` | Pull requirements (budget, condition, etc.) | LLM |
| 3 | `search_catalog` | Find matching products | `search_products` |
| 4 | `compare_products` | Side-by-side comparison | `compare_products` |
| 5 | `recommend` | Ranked recommendations | `recommend_products` |
| 6 | `capture_lead` | Save customer info | `capture_lead` |
| 7 | `generate_quote` | Create quotation | `generate_quotation` |
| 8 | `draft_email` | Write follow-up | `draft_email` |
| 9 | `build_response` | Compose reply to user | LLM |
| 10 | `error_handler` | Graceful recovery | — |

### Conditional Routing
```
classify_intent ──▶ extract_entities ──▶ [search | compare | recommend | lead | quote | email | respond]
     │                              
     └── error ──▶ error_handler ──▶ build_response
```

---

## 4. Tool Design (6 Tools)

| Tool | Input | Output | Logic |
|------|-------|--------|-------|
| `search_products` | query, filters | list[Product] | Fuzzy string match + filter by category, price range |
| `compare_products` | product_ids | comparison table | Side-by-side feature diff, highlight best values |
| `recommend_products` | requirements, top_k | ranked list | Score by condition match, budget fit, rating, popularity |
| `capture_lead` | customer_info | confirmation | Insert into SQLite, deduplicate by email |
| `generate_quotation` | product_ids, customer_info | quote | Build structured quote with pricing, terms, validity |
| `draft_email` | context, tone | email body | Professional template filled with context |

---

## 5. Data Layer

### SQLite Schema
```sql
products (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    description TEXT,
    price REAL,
    rating REAL,
    stock INTEGER,
    features TEXT,        -- JSON
    specs TEXT,           -- JSON
    condition_tags TEXT,  -- comma-separated
    image_url TEXT
)

leads (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    name TEXT,
    email TEXT,
    phone TEXT,
    organization TEXT,
    budget_range TEXT,
    condition TEXT,
    requirements TEXT,
    created_at TIMESTAMP,
    status TEXT
)

conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    content TEXT,
    timestamp TIMESTAMP,
    metadata TEXT
)

quotations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    lead_id INTEGER,
    products TEXT,        -- JSON array
    total_price REAL,
    discount REAL,
    validity_days INTEGER,
    terms TEXT,
    created_at TIMESTAMP
)
```

---

## 6. Error Handling Strategy

- **Tool-level**: Try/except with fallback to safe defaults. Log error, return empty + reason.
- **Node-level**: Wrapper that catches exceptions, sets `state["error"]`, routes to `error_handler`.
- **Graph-level**: Interrupt handler for unrecoverable errors. Set `requires_human = True`.
- **API-level**: FastAPI exception handlers return 500 with structured error JSON.
- **UI-level**: Streamlit shows error banners, retry button.

---

## 7. Edge Cases Identified

1. **Ambiguous intent**: User says "I need something for my clinic" → ask clarifying questions.
2. **No search results**: Product catalog has no match → suggest closest alternatives, ask to adjust filters.
3. **Missing customer info**: User asks for quote without providing contact → ask for info before proceeding.
4. **Duplicate lead**: Same email captured twice → update existing record, log deduplication.
5. **Invalid product IDs**: Comparison requested with non-existent IDs → filter valid, explain missing.
6. **Budget mismatch**: Recommendations exceed budget → flag alternatives, suggest financing.
7. **LLM API failure**: OpenAI API down → fallback to rule-based responses, log incident.
8. **Session timeout**: Long conversation gap → acknowledge gap, summarize context.

---

## 8. Project Structure

```
aquamax-agent/
├── .env                          # Secrets (gitignored)
├── .env.example                  # Template for secrets
├── .gitignore
├── README.md
├── requirements.txt
├── docs/
│   ├── architecture.md           # This file
│   ├── installation.md
│   └── deployment.md
├── src/
│   ├── config/         # Environment settings & constants
│   ├── core/           # LangGraph state, graph, agent, memory
│   ├── tools/          # 6 AI tools (search, compare, recommend, lead, quote, email)
│   ├── database/       # SQLite ORM, repository, seed data
│   ├── services/       # Business logic services
│   └── utils/          # Logging, helpers
├── api/                # FastAPI app & routers
├── ui/                 # Streamlit frontend
├── tests/              # Unit & integration tests
└── data/               # Sample product catalog
```

---

## 9. Technology Stack Justification

| Technology | Role | Why |
|------------|------|-----|
| **Python 3.11+** | Language | Type hints, `async`, modern syntax |
| **LangGraph** | Agent orchestration | State graphs, conditional routing, persistence |
| **LangChain** | LLM integration | Tool binding, message formatting, model switching |
| **OpenAI API** | LLM | OpenAI-compatible (Groq, Together, local models) |
| **SQLite** | Database | Zero-config, file-based, interview-portable |
| **SQLAlchemy** | ORM | Type-safe queries, migration-ready |
| **Pandas** | Data processing | Product filtering, comparison tables |
| **FastAPI** | Backend API | Async, auto-docs, Pydantic validation |
| **Streamlit** | Frontend | Rapid chat UI, minimal code |
| **Pydantic v2** | Validation | Type safety, JSON schema, settings management |
| **pytest** | Testing | Fixtures, parametrization, coverage |
| **python-dotenv** | Config | Environment-based secrets |
| **logging** | Observability | Structured logs, debuggability |

---

## 10. Resume & Interview Mapping

This project fills the following gaps in Viraj's profile:

| Gap | How This Project Fills It |
|-----|---------------------------|
| No LLM/GenAI experience | LangGraph + LangChain + OpenAI function calling |
| No API development | FastAPI with async endpoints, Pydantic, dependency injection |
| No AI Agent experience | Full state graph, tool calling, memory, error handling |
| No production Python | Type hints, logging, modular design, SOLID, testing |
| No deployment knowledge | Docker, deployment docs, CI/CD pipeline |
| No RAG/tool-use experience | Product search, recommendation, comparison tools |
| No full-stack demo | FastAPI backend + Streamlit frontend |

---

## 11. Future Improvements (Post-Interview)

1. **Vector DB + RAG**: Pinecone/Weaviate for semantic product search
2. **Voice Interface**: Whisper for speech-to-text, TTS for responses
3. **Multimodal**: Vision model for product image understanding
4. **Real-time pricing**: ERP integration for live inventory/pricing
5. **A/B testing**: Compare recommendation algorithms
6. **Analytics dashboard**: Power BI / Streamlit for lead conversion metrics
7. **Multi-tenant**: Support multiple equipment companies
8. **Authentication**: OAuth2, JWT tokens for sales rep accounts
9. **WebSocket**: Real-time chat for human handoff
10. **Docker + K8s**: Containerize, orchestrate, scale
