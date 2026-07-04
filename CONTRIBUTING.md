# Contributing to AquaMax AI Agent

Thank you for your interest in contributing! This project is primarily a **portfolio and educational project**, but contributions are welcome.

## How to Contribute

### Reporting Bugs
- Check if the issue already exists
- Provide clear reproduction steps
- Include your OS, Python version, and LLM provider

### Suggesting Enhancements
- Open an issue describing the enhancement
- Explain why it would be valuable
- Keep suggestions aligned with the project's scope (AI agent for sales/support)

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit with clear messages
6. Push to your fork and open a PR

## Development Setup

```bash
git clone https://github.com/indaisv/AquaMax-AI-Agent.git
cd AquaMax-AI-Agent
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Add your API key to .env
python -m src.database.seed
```

## Code Style
- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Keep functions focused (single responsibility)

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
