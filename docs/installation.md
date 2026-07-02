# Installation Guide

## Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/downloads)
- **OpenAI API Key** (or Groq, Together AI, or any OpenAI-compatible provider)

---

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/aquamax-agent.git
cd aquamax-agent
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```bash
OPENAI_API_KEY=sk-your-api-key-here
# Optional: use a different provider
# OPENAI_BASE_URL=https://api.groq.com/openai/v1
# MODEL_NAME=llama3-70b-8192
```

### 5. Initialize the Database

```bash
python -m src.database.seed
```

This creates the SQLite database and seeds it with 30+ rehabilitation equipment products.

### 6. Run the FastAPI Backend

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Open your browser to [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive API documentation.

### 7. Run the Streamlit UI (in a new terminal)

```bash
# Activate venv again
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS / Linux

streamlit run ui/app.py
```

Open your browser to [http://localhost:8501](http://localhost:8501).

---

## Verifying the Installation

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# List products
curl http://localhost:8000/products

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a TENS unit for back pain"}'
```

### Run the Test Suite

```bash
pytest tests/ -v
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated |
| `OPENAI_API_KEY not set` | Check `.env` file exists and key is valid |
| `Database locked` | Close any DB viewers; SQLite doesn't allow concurrent writes from different processes |
| `Port already in use` | Change `API_PORT` in `.env` or use `--port 8001` |
| `Streamlit not found` | Run `pip install streamlit` |

---

## Project Structure After Setup

```
aquamax-agent/
├── .env                          # Your API keys (gitignored)
├── venv/                         # Virtual environment
├── data/
│   └── aquamax.db                # SQLite database (created after seed)
├── src/                          # Source code
├── api/                          # FastAPI backend
├── ui/                           # Streamlit frontend
├── tests/                        # Test suite
└── docs/                         # Documentation
```
