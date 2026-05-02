"""FastAPI wrapper around TauricResearch/TradingAgents.

Exposes a REST API + minimal HTML UI to run multi-agent stock analysis on
Railway. Each request runs the full TradingAgentsGraph pipeline as a
background task; the frontend polls for completion and live logs.
"""
from __future__ import annotations

import collections
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# ── Monkey-patch requests to enforce a default timeout ──────────────
# yfinance (used by TradingAgents for data) calls requests without timeout,
# causing indefinite hangs when Yahoo Finance is slow or unresponsive.
_original_request = requests.Session.request

def _patched_request(self, *args, **kwargs):
    kwargs.setdefault("timeout", 60)
    return _original_request(self, *args, **kwargs)

requests.Session.request = _patched_request
# ────────────────────────────────────────────────────────────────────

INDEX_PATH = Path(__file__).parent / "index.html"
JOB_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "600"))

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
    version="0.2.0",
)

JOBS: dict[str, dict[str, Any]] = {}
JOB_REPORTS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
MAX_JOBS = 100
RESULTS_DIR = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", "/data/logs"))


class JobLogBuffer(logging.Handler):
    """Captures log lines into a per-job ring buffer."""

    def __init__(self, max_lines: int = 500):
        super().__init__()
        self.lines: collections.deque[str] = collections.deque(maxlen=max_lines)
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


JOB_LOGS: dict[str, JobLogBuffer] = {}


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
    progress: str | None = None
    created_at: str
    completed_at: str | None = None


def _trim_jobs() -> None:
    with JOBS_LOCK:
        if len(JOBS) <= MAX_JOBS:
            return
        sorted_ids = sorted(JOBS.keys(), key=lambda k: JOBS[k]["created_at"])
        for old_id in sorted_ids[: len(JOBS) - MAX_JOBS]:
            JOBS.pop(old_id, None)
            JOB_LOGS.pop(old_id, None)
            JOB_REPORTS.pop(old_id, None)


def _update_progress(job_id: str, msg: str) -> None:
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id]["progress"] = msg
    log.info("[%s] %s", job_id, msg)


def _run_analysis(job_id: str, req: AnalyzeRequest) -> None:
    """Synchronous entry point for the background task."""
    handler = JobLogBuffer()
    JOB_LOGS[job_id] = handler

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        _update_progress(job_id, "Importing TradingAgents library…")
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph

        _update_progress(job_id, "Configuring analysis graph…")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = req.llm_provider
        config["deep_think_llm"] = req.deep_think_llm
        config["quick_think_llm"] = req.quick_think_llm
        config["max_debate_rounds"] = req.max_debate_rounds
        config["max_risk_discuss_rounds"] = req.max_risk_discuss_rounds

        ta = TradingAgentsGraph(config=config)

        _update_progress(
            job_id,
            f"Running multi-agent analysis for {req.ticker.upper()} — "
            f"this typically takes 3–10 minutes…",
        )

        start = time.monotonic()
        final_state, decision = ta.propagate(req.ticker.upper(), req.date)
        elapsed = time.monotonic() - start

        report = {}
        if isinstance(final_state, dict):
            for key in (
                "market_report", "sentiment_report", "news_report",
                "fundamentals_report", "investment_debate_state",
                "trader_investment_decision", "risk_debate_state",
                "investment_plan", "final_trade_decision",
            ):
                val = final_state.get(key)
                if val is not None:
                    report[key] = str(val) if not isinstance(val, (str, dict, list)) else val
        JOB_REPORTS[job_id] = report

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["decision"] = str(decision)
            JOBS[job_id]["completed_at"] = _utc_now_iso()
            JOBS[job_id]["progress"] = f"Completed in {elapsed:.0f}s"
        log.info("[%s] completed in %.1fs", job_id, elapsed)

    except BaseException as exc:
        log.exception("[%s] failed", job_id)
        with JOBS_LOCK:
            if JOBS.get(job_id, {}).get("status") != "timed_out":
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = f"{type(exc).__name__}: {exc}"
                JOBS[job_id]["completed_at"] = _utc_now_iso()
                JOBS[job_id]["progress"] = "Failed"
    finally:
        root_logger.removeHandler(handler)


def _watchdog(job_id: str, timeout: int) -> None:
    """Marks a job as timed out after `timeout` seconds."""
    time.sleep(timeout)
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job and job["status"] == "running":
            job["status"] = "timed_out"
            job["error"] = (
                f"Analysis exceeded the {timeout}s timeout. "
                "This usually means a data source (Yahoo Finance) is unresponsive. "
                "Try again later or use a different date."
            )
            job["completed_at"] = _utc_now_iso()
            job["progress"] = "Timed out"
            log.warning("[%s] timed out after %ds", job_id, timeout)


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(INDEX_PATH, media_type="text/html")


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
        "progress": "Queued",
        "created_at": _utc_now_iso(),
        "completed_at": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = job

    background_tasks.add_task(_run_analysis, job_id, req)

    wd = threading.Thread(target=_watchdog, args=(job_id, JOB_TIMEOUT_SECONDS), daemon=True)
    wd.start()

    return JobResponse(**job)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str, tail: int = Query(default=50, ge=1, le=500)
) -> JSONResponse:
    handler = JOB_LOGS.get(job_id)
    if handler is None:
        raise HTTPException(status_code=404, detail="No logs for this job")
    lines = list(handler.lines)[-tail:]
    return JSONResponse(content={"job_id": job_id, "lines": lines, "total": len(handler.lines)})


@app.get("/api/jobs/{job_id}/report")
async def get_job_report(job_id: str) -> JSONResponse:
    """Full analysis report — all agent outputs from the pipeline."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Job status is '{job['status']}', report only available when completed")

    report = JOB_REPORTS.get(job_id)
    if not report:
        result_file = RESULTS_DIR / job["ticker"] / "TradingAgentsStrategy_logs" / f"full_states_log_{job['date']}.json"
        if result_file.exists():
            import json
            report = json.loads(result_file.read_text())
        else:
            report = {"decision": job.get("decision"), "note": "Detailed report not available in memory. The JSON log may be on the volume."}

    return JSONResponse(content={
        "job_id": job_id,
        "ticker": job["ticker"],
        "date": job["date"],
        "decision": job.get("decision"),
        "report": report,
    })


@app.get("/api/jobs/{job_id}/report/download")
async def download_job_report(job_id: str):
    """Download the full analysis as a JSON file."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result_file = RESULTS_DIR / job["ticker"] / "TradingAgentsStrategy_logs" / f"full_states_log_{job['date']}.json"
    if result_file.exists():
        return FileResponse(
            result_file,
            media_type="application/json",
            filename=f"{job['ticker']}_{job['date']}_analysis.json",
        )

    report = JOB_REPORTS.get(job_id)
    if report:
        import json
        content = {"ticker": job["ticker"], "date": job["date"], "decision": job.get("decision"), **report}
        headers = {"Content-Disposition": f'attachment; filename="{job["ticker"]}_{job["date"]}_analysis.json"'}
        return JSONResponse(content=content, headers=headers)

    raise HTTPException(status_code=404, detail="No report file found for this job")


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
