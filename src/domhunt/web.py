"""FastAPI web app: same RDAP-based checker, but with a tiny single-page UI.

Endpoints:
    GET  /            -> the single-page UI
    GET  /api/check   -> JSON: {results: [{domain, status, detail}, ...]}
    GET  /healthz     -> liveness probe for Render/Fly/etc.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from domhunt import __version__
from domhunt.checker import check_many
from domhunt.tlds import resolve_tlds

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


@app.get("/api/check")
async def api_check(
    name: str = Query(..., min_length=1, max_length=63),
    tlds: str | None = Query(None, description="Comma-separated TLDs or 'all'"),
) -> JSONResponse:
    name = name.strip().lower()
    if not _NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="Invalid domain label.")
    tld_list = resolve_tlds(tlds)
    if len(tld_list) > 40:
        raise HTTPException(status_code=400, detail="Too many TLDs (max 40 per request).")
    results = await check_many(name, tld_list, concurrency=10)
    return JSONResponse(
        {
            "name": name,
            "results": [
                {"domain": r.domain, "status": r.status.value, "detail": r.detail}
                for r in results
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
