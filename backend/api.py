"""
FastAPI backend for the Website Uptime Monitor.

Reuses all monitoring logic from the existing CLI (../website-uptime-monitor/main.py).
This file is a thin HTTP layer — no business logic lives here.

Start the server:
    cd backend
    uvicorn api:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Allow importing from the sibling directory (website-uptime-monitor/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "website-uptime-monitor"))

from main import validate_url, check_website, save_history, load_history
from config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ---------- app ----------

app = FastAPI(
    title="Website Uptime Monitor API",
    description="Check website availability, retrieve history, and view statistics.",
    version="1.0.0",
)

# Allow requests from the React dev server.
# In production, replace with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite (React)
        "http://localhost:3000",   # Create React App
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- request / response models ----------

class CheckRequest(BaseModel):
    url: str


class CheckResponse(BaseModel):
    url: str
    checked_at: str
    status: str           # "UP" or "DOWN"
    status_code: Optional[int]
    response_time_ms: Optional[float]
    error: Optional[str]


class HistoryRecord(BaseModel):
    url: str
    checked_at: str
    status: str
    status_code: Optional[int]
    response_time_ms: Optional[float]


class StatsResponse(BaseModel):
    total_checks: int
    up_count: int
    down_count: int
    uptime_percent: float
    average_response_ms: Optional[float]
    last_checked: Optional[str]


# ---------- endpoints ----------

@app.get("/")
def root():
    """Health check — confirms the API is running."""
    return {"status": "ok", "message": "Website Uptime Monitor API"}


@app.post("/check", response_model=CheckResponse)
def check(request: CheckRequest):
    """
    Check whether a website is up or down.

    Validates the URL, performs an HTTP request, saves the result to history,
    and returns the outcome.

    Returns 422 if the URL is invalid or blocked.
    """
    raw = request.url.strip()
    if not raw:
        raise HTTPException(status_code=422, detail="URL must not be empty.")

    url, validation_error = validate_url(raw)
    if validation_error:
        logger.warning("POST /check rejected URL %r: %s", raw, validation_error)
        raise HTTPException(status_code=422, detail=validation_error)

    status_code, uptime_status, elapsed, err_msg = check_website(url)
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_history(url, status_code, uptime_status, elapsed)
    logger.info("POST /check %s -> %s", url, uptime_status)

    return CheckResponse(
        url=url,
        checked_at=checked_at,
        status=uptime_status,
        status_code=status_code,
        response_time_ms=round(elapsed, 2) if elapsed is not None else None,
        error=err_msg,
    )


@app.get("/history", response_model=list[HistoryRecord])
def history(
    url: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """
    Return saved check history.

    Optional query parameters:
    - url: partial URL match filter  (?url=github)
    - status: "UP" or "DOWN"         (?status=DOWN)
    - limit: max records to return   (?limit=20)
    """
    if status and status.upper() not in ("UP", "DOWN"):
        raise HTTPException(status_code=422, detail="status must be UP or DOWN.")
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 1000.")

    records = load_history()

    if url:
        records = [r for r in records if url.lower() in r["url"].lower()]
    if status:
        records = [r for r in records if r["uptime_status"] == status.upper()]

    records = records[-limit:]

    return [
        HistoryRecord(
            url=r["url"],
            checked_at=r["checked_at"],
            status=r["uptime_status"],
            status_code=r.get("status_code"),
            response_time_ms=r.get("response_time_ms"),
        )
        for r in records
    ]


@app.get("/stats", response_model=StatsResponse)
def stats(url: Optional[str] = None):
    """
    Return uptime statistics calculated from saved history.

    Optional query parameter:
    - url: filter stats to one site  (?url=github.com)

    uptime_percent is the percentage of checks that returned UP.
    average_response_ms excludes failed checks (where response time is null).
    """
    records = load_history()

    if url:
        records = [r for r in records if url.lower() in r["url"].lower()]

    total = len(records)
    if total == 0:
        return StatsResponse(
            total_checks=0,
            up_count=0,
            down_count=0,
            uptime_percent=0.0,
            average_response_ms=None,
            last_checked=None,
        )

    up_count = sum(1 for r in records if r["uptime_status"] == "UP")
    down_count = total - up_count
    uptime_percent = round((up_count / total) * 100, 2)

    response_times = [r["response_time_ms"] for r in records if r.get("response_time_ms") is not None]
    average_response_ms = round(sum(response_times) / len(response_times), 2) if response_times else None

    last_checked = records[-1]["checked_at"] if records else None

    return StatsResponse(
        total_checks=total,
        up_count=up_count,
        down_count=down_count,
        uptime_percent=uptime_percent,
        average_response_ms=average_response_ms,
        last_checked=last_checked,
    )
