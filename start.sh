#!/bin/bash
set -e

PORT=${PORT:-8000}

mkdir -p "${TRADINGAGENTS_RESULTS_DIR:-/data/logs}" \
         "${TRADINGAGENTS_DATA_CACHE_DIR:-/data/cache}" \
         "$(dirname "${TRADINGAGENTS_MEMORY_LOG:-/data/memory/trading_memory.md}")"

echo "Starting TradingAgents API server on 0.0.0.0:${PORT}"
exec uvicorn app:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers 1 \
    --timeout-keep-alive 75 \
    --access-log
