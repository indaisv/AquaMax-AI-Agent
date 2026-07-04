# AquaMax AI Sales & Support Agent

<p align="center">
  <strong>Production-ready AI Agent for Rehabilitation Equipment Sales</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.40+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/LangGraph-0.2+-purple.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
</p>

---

## Overview

AquaMax AI is a **production-grade AI Agent** built for AquaMax Rehab Equipment, a rehabilitation and physiotherapy equipment company. It automates sales assistance and customer support through intelligent conversation — understanding requirements, searching a product catalog, recommending equipment, generating quotations, capturing leads, and drafting follow-up emails.

> **Built for:** AI Automation Engineer · AI Engineer · AI/ML Engineer · GenAI Engineer roles

---

## What This Agent Does

| Capability | Description |
|------------|-------------|
| **Understand Requirements** | Parses natural language to extract conditions, budgets, use-cases |
| **Search Catalog** | Keyword-based search over 40 rehab equipment products across 14 categories |
| **Compare Products** | Side-by-side feature comparison with highlighted differences |
| **Recommend Products** | AI-scored recommendations using rating, stock, condition match, and budget fit |
| **Capture Leads** | Automatically saves customer information to SQLite database |
| **Generate Quotations** | Structured quotes with GST (18%), discounts, and validity |
| **Draft Emails** | Professional follow-up emails in multiple tones |
| **Conversation Memory** | Remembers context across multi-turn sessions |
| **Tool Dispatch** | Rule-based tool execution (Groq/OpenAI-compatible) |
| **Error Recovery** | Graceful degradation with human handoff when needed |

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  FastAPI        │────▶│  LangGraph      │
│   (Chat Interface)     │  (REST API)     │     │  Agent          │
└─────────────────┘     └─────────────────┘     │  (State Graph)  │
                                                └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────┐
                              │                          │          │
                    ┌─────────▼────────┐    ┌───────────▼────────┐  │
                    │  LLM (Groq)      │    │  Tool Layer        │  │
                    │  · ReAct Reasoning    │  · Search Products │  │
                    │  · Response Build     │  · Compare Products│  │
                    └──────────────────┘    │  · Recommend       │  │
                                             │  · Capture Lead    │  │
                                             │  · Generate Quote  │  │
                                             │  · Draft Email     │  │
                                             └──────────┬─────────┘  │
                                                        │            │
                                             ┌──────────▼──────────┐ │
                                             │  SQLite Database    │◀┘
                                             │  · Products         │
                                             │  · Leads            │
                                             │  · Conversations    │
                                             │  · Quotations       │
                                             └─────────────────────┘
```

**Design:** Clean Architecture · SOLID · Repository Pattern · Dependency Injection · LangGraph State Graphs

Read the full [architecture document](docs/architecture.md) for design decisions, edge cases, and state graph design.

---

## Quick Start

### Prerequisites
- Python 3.11+
- An OpenAI-compatible API key (Groq recommended — free tier available)

### 1. Clone & Install

```bash
git clone https://github.com/indaisv/AquaMax-AI-Agent.git
cd AquaMax-AI-Agent
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — add your OpenAI-compatible API key
```

Example `.env` for Groq (free tier):
```env
OPENAI_API_KEY=gsk_your_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama3-70b-8192
```

### 3. Seed Database

```bash
python -m src.database.seed
```

This creates the SQLite database and inserts 40 rehabilitation equipment products.

### 4. Run FastAPI Backend

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Run Streamlit UI

In a **new terminal**:

```bash
venv\Scripts\activate        # Windows
streamlit run ui/app.py --server.port 8501
```

Open UI at: [http://localhost:8501](http://localhost:8501)

---

## Project Structure

```
AquaMax-AI-Agent/
├── src/
│   ├── config/         # Environment settings & constants (Pydantic v2)
│   ├── core/           # LangGraph state, graph, agent, memory
│   ├── tools/          # 6 AI tools (search, compare, recommend, lead, quote, email)
│   ├── database/       # SQLite ORM, repository pattern, seed data
│   ├── services/       # Business logic services
│   └── utils/          # Logging, helpers
├── api/                # FastAPI app & routers
├── ui/                 # Streamlit frontend
├── tests/              # Unit & integration tests
├── docs/               # Architecture, installation, deployment guides
├── data/               # Sample product catalog
├── CHANGELOG.md        # Version history
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE             # MIT License
└── README.md           # This file
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message to the AI agent |
| `GET`  | `/chat/{session_id}/history` | Retrieve conversation history |
| `GET`  | `/products` | List all products (with filters) |
| `GET`  | `/products/search` | Search products by query |
| `POST` | `/leads` | Create a lead manually |
| `GET`  | `/leads` | List all leads |
| `POST` | `/quotations` | Generate a quotation |
| `GET`  | `/quotations/{id}` | Get quotation by ID |
| `GET`  | `/health` | Health check |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Agent Framework** | LangGraph | State-machine graphs, conditional routing, persistence |
| **LLM Integration** | LangChain + Groq | OpenAI-compatible API, fast inference, free tier |
| **Backend API** | FastAPI | Async, auto-docs, Pydantic validation |
| **Frontend** | Streamlit | Rapid chat UI, minimal code |
| **Database** | SQLite + SQLAlchemy | Zero-config, file-based, interview-portable |
| **Data Processing** | Pandas | Product filtering, comparison tables |
| **Testing** | pytest | Fixtures, parametrization, coverage |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v
```

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for:
- Docker containerization
- Cloud deployment (Render, Railway, AWS)
- Environment setup for production

Quick Docker start:
```bash
docker-compose up --build
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Design decisions, state graph, edge cases |
| [docs/installation.md](docs/installation.md) | Step-by-step installation guide |
| [docs/deployment.md](docs/deployment.md) | Docker, cloud, and CI/CD deployment |
| [DELIVERABLES.md](DELIVERABLES.md) | Resume bullets, LinkedIn post, interview Q&A |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## Why This Project

This project demonstrates **end-to-end AI agent engineering** — not a simple chatbot, but a full business automation system:

- **LLM Orchestration:** LangGraph state graphs with conditional routing and tool dispatch
- **API Development:** FastAPI with async endpoints, dependency injection, Pydantic validation
- **Database Design:** SQLAlchemy ORM with repository pattern, 40-product catalog
- **Full-Stack Delivery:** Backend API + Streamlit frontend
- **Production Thinking:** Logging, error handling, environment configuration, testing
- **Business Logic:** Lead capture, quotation generation, email drafting, product recommendation

---

## License

[MIT](LICENSE) — Built for portfolio and educational purposes.

---

## Author

**Viraj Indais** — AI Automation Engineer | Data Scientist

- [LinkedIn](https://linkedin.com/in/viraj-indais)
- [GitHub](https://github.com/indaisv)
- [Email](mailto:indaisviraj@gmail.com)

---

<p align="center">
  <sub>Version 1.0 · Built with LangGraph · FastAPI · Streamlit · Groq</sub>
</p>
