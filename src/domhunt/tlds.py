"""Curated lists of TLDs to query.

The default set covers the TLDs most relevant to indie hackers and developers
hunting for a project domain — short, memorable, and commonly available via
major registrars.
"""

# Order matters: the most desirable TLDs come first so they render at the top
# of the output table.
DEFAULT_TLDS: tuple[str, ...] = (
    "com",
    "io",
    "dev",
    "app",
    "ai",
    "co",
    "net",
    "org",
    "me",
    "xyz",
    "sh",
    "fm",
)

# Larger curated set, opt-in via --tlds all
EXTENDED_TLDS: tuple[str, ...] = DEFAULT_TLDS + (
    "tech",
    "tools",
    "studio",
    "design",
    "blog",
    "site",
    "shop",
    "store",
    "online",
    "cloud",
    "page",
    "link",
    "click",
    "info",
    "biz",
    "us",
    "uk",
    "eu",
    "de",
    "fr",
)


def resolve_tlds(spec: str | None) -> list[str]:
    """Translate a user-provided spec into a concrete list of TLDs.

    Accepts:
        None         -> default curated list
        "all"        -> extended curated list
        "com,io,..." -> comma-separated user list (leading dots are stripped)
    """
    if spec is None:
        return list(DEFAULT_TLDS)
    if spec.strip().lower() == "all":
        return list(EXTENDED_TLDS)
    return [t.strip().lstrip(".").lower() for t in spec.split(",") if t.strip()]
