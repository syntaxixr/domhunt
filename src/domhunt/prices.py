"""Approximate retail registration prices per TLD.

Source: Porkbun retail tier (as of early 2026). Porkbun is consistently the
cheapest mainstream registrar with no upsells. Renewal prices are usually
identical to registration price (which is rare — most registrars upsell on
renewal), so first-year and renewal are treated as the same here.

These numbers WILL drift over time. They are intentionally approximate and
shown to give the user a ballpark, with a deep link to the registrar that has
the real, current number.
"""

from __future__ import annotations

# USD per year, Porkbun retail. None means unknown / premium-tier only.
PRICES_USD: dict[str, float] = {
    "com": 10.0,
    "net": 12.0,
    "org": 11.0,
    "io": 38.0,
    "dev": 15.0,
    "app": 14.0,
    "ai": 70.0,
    "co": 26.0,
    "me": 17.0,
    "xyz": 2.0,
    "sh": 80.0,
    "fm": 110.0,
    "tech": 5.0,
    "tools": 22.0,
    "studio": 21.0,
    "design": 35.0,
    "blog": 21.0,
    "site": 4.0,
    "shop": 4.0,
    "store": 5.0,
    "online": 2.0,
    "cloud": 9.0,
    "page": 8.0,
    "link": 9.0,
    "click": 6.0,
    "info": 4.0,
    "biz": 17.0,
    "us": 9.0,
    "uk": 8.0,
    "eu": 9.0,
    "de": 7.0,
    "fr": 9.0,
}


def price_for(tld: str) -> float | None:
    """Return USD/year for a TLD, or None if we don't have data."""
    return PRICES_USD.get(tld.lstrip(".").lower())


def porkbun_url(domain: str) -> str:
    """Deep link to Porkbun's checkout for a specific domain."""
    return f"https://porkbun.com/checkout/search?q={domain}"
