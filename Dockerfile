FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir git+https://github.com/TauricResearch/TradingAgents.git@main

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py templates.py ./
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

ENV TRADINGAGENTS_RESULTS_DIR=/data/logs \
    TRADINGAGENTS_DATA_CACHE_DIR=/data/cache \
    TRADINGAGENTS_MEMORY_LOG=/data/memory/trading_memory.md \
    PORT=8000

RUN mkdir -p /data/logs /data/cache /data/memory && \
    chmod -R 777 /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

CMD ["/usr/local/bin/start.sh"]
