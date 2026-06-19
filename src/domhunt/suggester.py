"""Generate creative name variations when the exact name is taken everywhere.

The variations follow patterns commonly seen across startups and indie projects:

    Prefixes:  get-, try-, use-, my-, the-, go-
    Suffixes:  -app, -hq, -hub, -labs, -io, -ly
    Glued:     X+app, X+hq, get+X, try+X
    Domain hacks: word naturally ending in the TLD (limited; we just hint).
"""

from __future__ import annotations

PREFIXES: tuple[str, ...] = ("get", "try", "use", "my", "the", "go")
SUFFIXES: tuple[str, ...] = ("app", "hq", "hub", "labs", "io", "ly")


def variations(name: str, limit: int = 12) -> list[str]:
    """Produce up to `limit` candidate names, ordered from most natural to less.

    The list is deduplicated and never contains the original name.
    """
    name = name.strip().lower().lstrip("-").rstrip("-")
    if not name:
        return []

    out: list[str] = []
    seen: set[str] = {name}

    def add(candidate: str) -> None:
        candidate = candidate.strip("-")
        if candidate and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)

    # 1. Glued suffixes feel like a real product name (e.g. "acmehq", "acmeapp")
    for s in SUFFIXES:
        add(f"{name}{s}")

    # 2. Hyphenated suffixes (more readable for long names)
    for s in SUFFIXES:
        add(f"{name}-{s}")

    # 3. Prefixed forms ("getacme", "tryacme")
    for p in PREFIXES:
        add(f"{p}{name}")

    # 4. Hyphenated prefixes ("get-acme")
    for p in PREFIXES:
        add(f"{p}-{name}")

    return out[:limit]
