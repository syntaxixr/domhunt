"""Async domain availability checking via the public RDAP gateway.

We use https://rdap.org/, which transparently routes a query to the correct
authoritative RDAP server for the TLD. The response status tells us whether
the domain is registered:

    200 OK        -> domain is registered (taken)
    404 Not Found -> domain is not registered (available)
    anything else -> unknown / error

RDAP is the modern successor to WHOIS (RFC 7480) and is supported by all major
registries. This keeps the implementation tiny — no per-TLD whois adapters.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum

import httpx

from domhunt.prices import porkbun_url, price_for

RDAP_GATEWAY = "https://rdap.org/domain/"
DEFAULT_TIMEOUT = 8.0
DEFAULT_CONCURRENCY = 10


class Status(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class CheckResult:
    domain: str
    status: Status
    detail: str = ""
    price_usd: float | None = field(default=None)
    buy_url: str | None = field(default=None)


def _enrich(result: CheckResult) -> CheckResult:
    """Attach price + buy URL to a result based on its TLD."""
    tld = result.domain.rsplit(".", 1)[-1]
    result.price_usd = price_for(tld)
    result.buy_url = porkbun_url(result.domain)
    return result


async def check_one(
    client: httpx.AsyncClient,
    domain: str,
    semaphore: asyncio.Semaphore,
) -> CheckResult:
    """Check a single domain. Never raises — encodes failure into the result."""
    async with semaphore:
        try:
            resp = await client.get(RDAP_GATEWAY + domain, timeout=DEFAULT_TIMEOUT)
        except httpx.TimeoutException:
            return _enrich(CheckResult(domain, Status.UNKNOWN, "timeout"))
        except httpx.HTTPError as exc:
            return _enrich(CheckResult(domain, Status.UNKNOWN, f"http error: {exc}"))

    if resp.status_code == 200:
        return _enrich(CheckResult(domain, Status.TAKEN))
    if resp.status_code == 404:
        return _enrich(CheckResult(domain, Status.AVAILABLE))
    # rdap.org returns 400 for TLDs without RDAP support — surface that clearly.
    if resp.status_code == 400:
        return _enrich(CheckResult(domain, Status.UNKNOWN, "TLD has no RDAP server"))
    return _enrich(CheckResult(domain, Status.UNKNOWN, f"HTTP {resp.status_code}"))


async def check_many(
    name: str,
    tlds: list[str],
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[CheckResult]:
    """Check `name.<tld>` for every tld in `tlds`. Preserves input order."""
    domains = [f"{name}.{tld}" for tld in tlds]
    semaphore = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": "domhunt/0.1 (+https://github.com/syntaxixr/domhunt)"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        tasks = [check_one(client, d, semaphore) for d in domains]
        return await asyncio.gather(*tasks)
