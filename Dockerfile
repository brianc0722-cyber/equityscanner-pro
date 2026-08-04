# EquityScanner Pro - Multi-stage friendly Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . .

# Make sure PYTHONPATH includes the project root
ENV PYTHONPATH=.

# Default command (overridden by docker-compose)
CMD ["python", "run_all.py"]
