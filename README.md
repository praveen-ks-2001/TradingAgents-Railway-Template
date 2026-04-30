![TradingAgents logo](https://github.com/TauricResearch/TradingAgents/raw/main/assets/TauricResearch.png)

# Deploy and Host TradingAgents on Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/trading-agents?referralCode=QXdhdr)

TradingAgents is an open-source multi-agent LLM framework by Tauric Research that mirrors the dynamics of a real trading firm — analysts, researchers, traders, and risk managers debate and converge on a buy/hold/sell recommendation for any ticker. Self-host TradingAgents on Railway to run the full agent graph through a clean web UI and REST API, without exposing your LLM API keys to a third-party service.

This Railway template wraps the upstream Python package in a FastAPI service so you can submit `(ticker, date)` analyses from a browser, poll job status, and inspect decisions through `/docs`. It bundles a persistent volume for analysis logs, agent memory, and market-data cache so multi-day research stays available across redeploys.

## Getting Started with TradingAgents on Railway

Once the deploy finishes, open the generated `*.up.railway.app` URL — the home page is a single form for ticker, date, LLM provider, and debate rounds. Pick `OPENAI` (the default), submit, and the job will run in the background; the page polls every three seconds until the agent graph returns a decision. Visit `/docs` to use the auto-generated Swagger UI directly, or `POST /api/analyze` from any HTTP client. All historic jobs persist in `/data/logs` on the mounted volume.

![TradingAgents dashboard screenshot](https://res.cloudinary.com/asset-cloudinary/image/upload/v1777574797/dfbd38a4-2d57-473e-abcf-057882957bae.png)

## About Hosting TradingAgents

TradingAgents orchestrates seven specialized LLM agents through a LangGraph state machine: fundamentals analyst, sentiment analyst, news analyst, technical analyst, bull researcher, bear researcher, and a trader who weighs all four reports against a risk manager. Each agent has its own prompt, tool access, and memory.

Key features:
- Multi-provider LLM support (OpenAI, Anthropic, Google, DeepSeek, Qwen, GLM, OpenRouter, local Ollama)
- Configurable debate depth — more rounds = more deliberation, more tokens
- yfinance built in (free); Alpha Vantage optional for premium data
- Persistent agent memory + decision log on disk
- Built-in checkpoints — resume long analyses after a redeploy

## Why Deploy TradingAgents on Railway

Railway is the fastest path from `git push` to a publicly reachable agent endpoint:

- One-click Docker deploy from this template
- Persistent volume pre-mounted for memory, cache, and logs
- Generated public domain with HTTPS — usable from any client
- Built-in env var management for LLM API keys
- Bump CPU/RAM with a slider when debate rounds get heavy

## Common Use Cases

- Run automated nightly analyses on a watchlist via cron + the REST API
- Compare LLM providers' decisions on the same ticker as a research baseline
- Power an internal Slack bot that returns multi-agent deliberation on demand
- Back-test agent decisions against historical data using the `date` parameter

## Dependencies for TradingAgents on Railway

This template runs as a single service:
- TradingAgents — Python 3.12-slim image, installs `tradingagents` from `github.com/TauricResearch/TradingAgents` plus a FastAPI/uvicorn wrapper

### Environment Variables Reference

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI provider key (required if `llm_provider=openai`) | — |
| `ANTHROPIC_API_KEY` | Anthropic Claude key | — |
| `GOOGLE_API_KEY` | Google Gemini key | — |
| `DEEPSEEK_API_KEY` | DeepSeek key | — |
| `OPENROUTER_API_KEY` | OpenRouter key (access many models) | — |
| `ALPHA_VANTAGE_API_KEY` | Premium market data (optional) | yfinance fallback |
| `TRADINGAGENTS_RESULTS_DIR` | Decision log path | `/data/logs` |
| `TRADINGAGENTS_DATA_CACHE_DIR` | Market-data cache path | `/data/cache` |
| `TRADINGAGENTS_MEMORY_LOG` | Persistent agent memory file | `/data/memory/trading_memory.md` |
| `PORT` | HTTP port (Railway sets automatically) | `8000` |

### Deployment Dependencies

- Source: https://github.com/TauricResearch/TradingAgents
- Latest release: v0.2.4
- Runtime: Python 3.12 (Debian slim base)
- License: Apache 2.0
- Volume: `/data` (1 GB recommended)

## Hardware Requirements for Self-Hosting TradingAgents

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Storage | 1 GB volume | 5 GB volume |
| Runtime | Python 3.10+ | Python 3.12 |

LangChain + multi-agent debate is memory-hungry; 2 GB will OOM on long debates. Bump to 4 GB for production use.

## Self-Hosting TradingAgents

The fastest path is the Railway template above. To run it locally for development, the upstream supports `pip install` plus a CLI:

```
git clone https://github.com/TauricResearch/TradingAgents
cd TradingAgents
python -m venv .venv && source .venv/bin/activate
pip install .
export OPENAI_API_KEY=sk-...
tradingagents
```

To call the analysis programmatically — useful when integrating with another service — import the graph directly:

```
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["deep_think_llm"] = "gpt-4o"
config["quick_think_llm"] = "gpt-4o-mini"

ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

The Railway template wraps exactly this call inside a FastAPI background task.

## How Much Does TradingAgents Cost to Self-Host?

The TradingAgents framework is fully open source under Apache 2.0 — no per-seat fees, no commercial tier. On Railway you only pay for compute, RAM, and the volume; with light usage that's under $10/month. The real cost is the LLM tokens: a single analysis with `gpt-4o` deep-think + `gpt-4o-mini` quick-think and one debate round runs roughly $0.20–$0.80 per ticker. Doubling debate rounds roughly doubles cost.

## FAQ

**What is TradingAgents and why self-host it?**
TradingAgents is a multi-agent LLM framework that simulates a trading firm's research workflow. Self-hosting on Railway keeps your tickers, prompts, and decisions on infrastructure you control instead of routing them through a third-party SaaS.

**What does this Railway template deploy?**
A single Python service that installs the upstream `tradingagents` package, wraps it in FastAPI, and exposes a web UI plus REST API at `/`, `/docs`, and `/api/analyze`. A persistent volume at `/data` stores logs, agent memory, and the market-data cache.

**Why does this template need a persistent volume?**
TradingAgents writes decision logs, market-data caches, and the agent memory file across runs. A Railway volume keeps them across redeploys so the agents can reference prior debates.

**Can I use models other than OpenAI when self-hosting TradingAgents?**
Yes. Set the matching env var (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, etc.) and pick the provider in the home-page form or pass `llm_provider` in the API body.

**How long does a single analysis take to run on Railway?**
With one debate round and `gpt-4o-mini` quick-think, expect 60–180 seconds. Heavier models or higher debate counts can push this past 5 minutes — bump RAM and the uvicorn timeout if you hit edge timeouts.

**Is this template safe to use for live trading decisions?**
The upstream project is research-grade and explicitly states it is not financial, investment, or trading advice. Treat the output as a reasoning artifact, not a signal.
