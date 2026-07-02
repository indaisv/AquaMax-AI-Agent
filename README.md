# AquaMax AI Sales & Support Agent

A production-ready AI Agent built for **AquaMax Rehab Equipment** that automates sales assistance and customer support through intelligent conversation, product recommendation, quotation generation, and lead capture.

> **Built with:** LangGraph · LangChain · FastAPI · Streamlit · SQLite · OpenAI

---

## What This Agent Does

| Capability | Description |
|------------|-------------|
| **Understand Requirements** | Parses natural language to extract conditions, budgets, use-cases |
| **Search Catalog** | Fuzzy + structured search over 30+ rehab equipment products |
| **Compare Products** | Side-by-side feature comparison with highlighted differences |
| **Recommend Products** | Ranked recommendations with explanations |
| **Capture Leads** | Automatically saves customer information to SQLite database |
| **Generate Quotations** | Structured quotes with pricing, discounts, and validity |
| **Draft Emails** | Professional follow-up emails in multiple tones |
| **Conversation Memory** | Remembers context across a multi-turn session |
| **Tool Calling** | Uses 6 specialized tools automatically via function calling |
| **Error Recovery** | Graceful degradation when tools or APIs fail |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/indaisv/aquamax-agent.git
cd aquamax-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — add your OpenAI-compatible API key
```

### 3. Seed Database

```bash
python -m src.database.seed
```

### 4. Run FastAPI Backend

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Run Streamlit UI

```bash
streamlit run ui/app.py
```

Open UI at: [http://localhost:8501](http://localhost:8501)

---

## Project Structure

```
aquamax-agent/
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
├── docs/               # Architecture & deployment guides
└── data/               # Sample product catalog
```

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
                    │  LLM (OpenAI)    │    │  Tool Layer        │  │
                    │  · Intent Classify    │  · Search Products │  │
                    │  · Entity Extract     │  · Compare Products│  │
                    │  · Response Build     │  · Recommend       │  │
                    └──────────────────┘    │  · Capture Lead    │  │
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

Read the full [architecture document](docs/architecture.md) for design decisions, edge cases, and state graph design.

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

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI or compatible API key |
| `OPENAI_BASE_URL` | No | — | Custom base URL (e.g., Groq, Together) |
| `MODEL_NAME` | No | `gpt-4o-mini` | LLM model to use |
| `DATABASE_URL` | No | `sqlite:///data/aquamax.db` | SQLite path |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_PORT` | No | `8000` | FastAPI port |
| `UI_PORT` | No | `8501` | Streamlit port |

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for:
- Docker containerization
- Cloud deployment (Render, Railway, AWS)
- Environment setup for production

---

## License

MIT — Built for portfolio and educational purposes.

---

## Author

**Viraj Indais** — AI Automation Engineer | Data Scientist
- [LinkedIn](https://linkedin.com/in/viraj-indais)
- [GitHub](https://github.com/indaisv)
- [Email](mailto:indaisviraj@gmail.com)
