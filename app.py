"""FastAPI wrapper around TauricResearch/TradingAgents.

Exposes a REST API + minimal HTML UI to run multi-agent stock analysis on
Railway. Each request runs the full TradingAgentsGraph pipeline as a
background task; the frontend polls for completion.
"""
from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from templates import INDEX_HTML

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("tradingagents-api")

app = FastAPI(
    title="TradingAgents API",
    description=(
        "Multi-agent LLM trading framework by Tauric Research. "
        "Self-hosted on Railway."
    ),
    version="0.1.0",
)

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
MAX_JOBS = 100


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _provider_key_present(provider: str) -> bool:
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": None,
    }
    env_key = mapping.get(provider.lower())
    if env_key is None:
        return True
    return bool(os.getenv(env_key))


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, examples=["NVDA"])
    date: str = Field(..., examples=["2026-01-15"])
    llm_provider: str = Field("openai")
    deep_think_llm: str = Field("gpt-4o")
    quick_think_llm: str = Field("gpt-4o-mini")
    max_debate_rounds: int = Field(1, ge=1, le=5)
    max_risk_discuss_rounds: int = Field(1, ge=1, le=5)


class JobResponse(BaseModel):
    job_id: str
    status: str
    ticker: str
    date: str
    decision: str | None = None
    error: str | None = None
    created_at: str
    completed_at: str | None = None


def _trim_jobs() -> None:
    with JOBS_LOCK:
        if len(JOBS) <= MAX_JOBS:
            return
        sorted_ids = sorted(JOBS.keys(), key=lambda k: JOBS[k]["created_at"])
        for old_id in sorted_ids[: len(JOBS) - MAX_JOBS]:
            JOBS.pop(old_id, None)


def _run_analysis(job_id: str, req: AnalyzeRequest) -> None:
    """Synchronous entry point for the background task. Heavy imports are
    done lazily so the API process boots fast even before LangChain is loaded.
    """
    log.info("[%s] starting %s @ %s", job_id, req.ticker, req.date)
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = req.llm_provider
        config["deep_think_llm"] = req.deep_think_llm
        config["quick_think_llm"] = req.quick_think_llm
        config["max_debate_rounds"] = req.max_debate_rounds
        config["max_risk_discuss_rounds"] = req.max_risk_discuss_rounds

        ta = TradingAgentsGraph(config=config)
        _, decision = ta.propagate(req.ticker.upper(), req.date)

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["decision"] = str(decision)
            JOBS[job_id]["completed_at"] = _utc_now_iso()
        log.info("[%s] completed", job_id)
    except Exception as exc:
        log.exception("[%s] failed", job_id)
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = f"{type(exc).__name__}: {exc}"
            JOBS[job_id]["completed_at"] = _utc_now_iso()


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index() -> str:
    return INDEX_HTML


@app.post("/api/analyze", response_model=JobResponse)
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks) -> JobResponse:
    if not _provider_key_present(req.llm_provider):
        raise HTTPException(
            status_code=400,
            detail=(
                f"API key for provider '{req.llm_provider}' not configured. "
                f"Set the corresponding env var (e.g. OPENAI_API_KEY)."
            ),
        )

    _trim_jobs()
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "running",
        "ticker": req.ticker.upper(),
        "date": req.date,
        "decision": None,
        "error": None,
        "created_at": _utc_now_iso(),
        "completed_at": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = job

    background_tasks.add_task(_run_analysis, job_id, req)
    return JobResponse(**job)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)


@app.get("/api/jobs")
async def list_jobs() -> JSONResponse:
    with JOBS_LOCK:
        jobs = sorted(
            JOBS.values(),
            key=lambda j: j["created_at"],
            reverse=True,
        )
    return JSONResponse(content=jobs)


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    """Expose which provider keys are configured (does NOT leak the keys)."""
    return {
        "providers_available": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "google": bool(os.getenv("GOOGLE_API_KEY")),
            "xai": bool(os.getenv("XAI_API_KEY")),
            "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        },
        "data_sources": {
            "alpha_vantage": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
            "yfinance": True,
        },
    }
