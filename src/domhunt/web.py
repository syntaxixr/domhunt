"""FastAPI web app: same RDAP-based checker, but with a tiny single-page UI.

Endpoints:
    GET  /            -> the single-page UI
    GET  /api/check   -> JSON: {results: [{domain, status, detail}, ...]}
    GET  /healthz     -> liveness probe for Render/Fly/etc.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from domhunt import __version__
from domhunt.checker import check_many
from domhunt.suggester import variations
from domhunt.tlds import resolve_tlds

_MAX_TLDS = 40
_MAX_CANDIDATES = 12

_STATIC_DIR = Path(__file__).parent / "static"
_NAME_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")

app = FastAPI(
    title="domhunt",
    version=__version__,
    description="Check domain availability across many TLDs in one request.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


def _validate_query(name: str, tlds: str | None) -> tuple[str, list[str]]:
    name = name.strip().lower()
    if not _NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Invalid domain label.")
    tld_list = resolve_tlds(tlds)
    if len(tld_list) > _MAX_TLDS:
        raise HTTPException(
            status_code=400, detail=f"Too many TLDs (max {_MAX_TLDS} per request)."
        )
    return name, tld_list


def _serialize(results) -> list[dict]:
    return [
        {
            "domain": r.domain,
            "status": r.status.value,
            "detail": r.detail,
            "price_usd": r.price_usd,
            "buy_url": r.buy_url,
        }
        for r in results
    ]


@app.get("/api/check")
async def api_check(
    name: str = Query(..., min_length=1, max_length=63),
    tlds: str | None = Query(None, description="Comma-separated TLDs or 'all'"),
) -> JSONResponse:
    name, tld_list = _validate_query(name, tlds)
    results = await check_many(name, tld_list, concurrency=10)
    return JSONResponse({"name": name, "results": _serialize(results)})


@app.get("/api/suggest")
async def api_suggest(
    name: str = Query(..., min_length=1, max_length=63),
    tlds: str | None = Query(None, description="Comma-separated TLDs or 'all'"),
) -> JSONResponse:
    """Generate creative variations and check each across the requested TLDs."""
    name, tld_list = _validate_query(name, tlds)
    candidates = variations(name, limit=_MAX_CANDIDATES)
    chunks = await asyncio.gather(
        *(check_many(c, tld_list, concurrency=10) for c in candidates)
    )
    return JSONResponse(
        {
            "name": name,
            "candidates": [
                {"name": c, "results": _serialize(rs)} for c, rs in zip(candidates, chunks)
            ],
        }
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


def run() -> None:
    """Entry point for the `domhunt-web` console script."""
    import os

    import uvicorn

    uvicorn.run(
        "domhunt.web:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        log_level="info",
    )


if __name__ == "__main__":
    run()
