# Dockerfile for AquaMax AI Agent
# Build: docker build -t aquamax-agent .
# Run: docker run -p 8000:8000 -p 8501:8501 aquamax-agent

FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose ports for FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Default command: run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
