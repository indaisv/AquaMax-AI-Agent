# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-04

### Added
- Production-ready AI Sales & Support Agent for AquaMax Rehab Equipment
- LangGraph state-machine workflow with rule-based tool dispatch
- 6 AI tools: search_products, compare_products, recommend_products, capture_lead, generate_quotation, draft_email
- FastAPI backend with auto-generated OpenAPI docs
- Streamlit frontend with chat interface, product catalog, and leads dashboard
- SQLite database with 40 rehabilitation equipment products across 14 categories
- SQLAlchemy ORM with repository pattern
- Conversation memory with session persistence
- Graceful error handling with human handoff capability
- Docker support (Dockerfile + docker-compose.yml)
- Comprehensive test suite (unit + integration tests)
- Complete documentation: README, architecture guide, installation guide, deployment guide
- Interview prep materials: Q&A, resume bullets, LinkedIn post

### Technical Details
- **Agent Framework:** LangGraph (state graphs, conditional routing)
- **LLM Integration:** LangChain + Groq (OpenAI-compatible API)
- **Backend:** FastAPI with async endpoints, Pydantic v2 validation
- **Frontend:** Streamlit
- **Database:** SQLite with SQLAlchemy ORM
- **Data Processing:** Pandas
- **Testing:** pytest + pytest-asyncio

### Known Limitations
- SQLite is file-based and not suitable for high-concurrency production use
- LLM responses are limited by `max_tokens` (may cut off for very long responses)
- Keyword search is basic; semantic search would improve relevance
- No authentication or multi-tenancy support
- No WebSocket for real-time updates

## Future Roadmap
See [DELIVERABLES.md](DELIVERABLES.md) for detailed future improvements.
