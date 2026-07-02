# Deployment Guide

## Local Deployment

See [installation.md](installation.md) for local development setup.

---

## Docker Deployment (Recommended for Production)

### 1. Create a Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Run FastAPI by default
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create docker-compose.yml

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///data/aquamax.db
    volumes:
      - ./data:/app/data
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  ui:
    build: .
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://api:8000
    depends_on:
      - api
    command: streamlit run ui/app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. Deploy with Docker Compose

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## Cloud Deployment

### Render (Recommended for Beginners)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Add `OPENAI_API_KEY` secret
5. Deploy!

### Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project
3. Deploy from GitHub repo
4. Add environment variables in Railway dashboard
5. Deploy automatically

### AWS (EC2)

```bash
# SSH into EC2
ssh -i key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Clone and deploy
git clone https://github.com/<your-username>/aquamax-agent.git
cd aquamax-agent

# Create .env
echo "OPENAI_API_KEY=sk-your-key" > .env

# Build and run
sudo docker-compose up --build -d
```

---

## Environment Variables for Production

| Variable | Production Value | Notes |
|----------|-----------------|-------|
| `OPENAI_API_KEY` | Your secure key | Use secrets manager, never commit |
| `OPENAI_BASE_URL` | Provider URL | Optional for Groq/Together |
| `MODEL_NAME` | `gpt-4o` | Use production-grade model |
| `DATABASE_URL` | `sqlite:///data/aquamax.db` | Change to PostgreSQL for scale |
| `LOG_LEVEL` | `INFO` | Use `WARNING` for less noise |
| `API_PORT` | `8000` | Or use `$PORT` for cloud platforms |

---

## Scaling Considerations

| Scale | Recommendation |
|-------|----------------|
| 1-10 users | SQLite + single instance |
| 10-100 users | PostgreSQL + 2-3 FastAPI instances |
| 100+ users | PostgreSQL + Redis (caching) + load balancer |
| Enterprise | Kubernetes + managed DB + observability stack |

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Render
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

---

## Monitoring & Logging

- **Local**: Check `logs/` directory or console output
- **Production**: Use structured JSON logging → forward to CloudWatch/Datadog
- **Metrics**: Add Prometheus metrics endpoint for FastAPI
- **Alerts**: Set up alerts for API errors, LLM latency, and DB connection issues
