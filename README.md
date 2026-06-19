# domhunt

> Check domain name availability across many TLDs in one command — from your terminal.

You have a project name in mind. You want to know if `acme.com`, `acme.io`,
`acme.dev`, `acme.app`, `acme.ai`, `acme.co`, ... are taken. Opening Namecheap
or GoDaddy and typing each one is slow. `domhunt` does it in one go.

```text
$ domhunt acme

                domhunt — 'acme'
+-----------+----------------+------------------------+
| Domain    | Status         | Detail                 |
+-----------+----------------+------------------------+
| acme.com  | [-] taken      |                        |
| acme.io   | [-] taken      |                        |
| acme.dev  | [+] available  |                        |
| acme.app  | [+] available  |                        |
| acme.ai   | [-] taken      |                        |
| acme.co   | [-] taken      |                        |
| acme.net  | [-] taken      |                        |
| acme.org  | [-] taken      |                        |
| acme.me   | [-] taken      |                        |
| acme.xyz  | [+] available  |                        |
| acme.sh   | [-] taken      |                        |
| acme.fm   | [?] unknown    | TLD has no RDAP server |
+-----------+----------------+------------------------+

3 available of 12 checked.
```

## Why

- Hunting for a project name? You don't want to open 12 registrar tabs.
- Existing online tools are slow, full of ads, or upsell you on premium plans.
- This is just a tiny CLI: one query, one table, done.

## Install

```bash
pip install domhunt
```

Requires Python 3.10+.

## Usage

```bash
# Default curated TLD set (12 developer-friendly TLDs)
domhunt myproject

# Custom list
domhunt acme --tlds com,io,dev,app

# Extended set (~30 TLDs)
domhunt acme --tlds all

# Only print the available ones (useful in scripts)
domhunt newco --tlds all --available-only
```

| Flag                | Description                                       |
| ------------------- | ------------------------------------------------- |
| `--tlds`            | Comma-separated TLDs, or `all` for extended list. |
| `-c, --concurrency` | Max parallel RDAP queries (default `10`).         |
| `-a, --available-only` | Hide taken/unknown domains.                    |
| `-h, --help`        | Show help.                                        |
| `--version`         | Show version.                                     |

## How it works

`domhunt` queries the public [RDAP](https://datatracker.ietf.org/doc/html/rfc7480)
gateway at <https://rdap.org/>. RDAP is the modern successor to WHOIS (defined
by ICANN and adopted by all major registries) and returns clean JSON over HTTPS:

- HTTP `404` → domain is **available**
- HTTP `200` → domain is **taken**
- HTTP `400` → that TLD doesn't expose an RDAP server (rare; falls back to `unknown`)

Checks run concurrently with `asyncio` + `httpx`, so 30 TLDs take a couple of
seconds, not 30.

## Roadmap

- [ ] Suggest creative variations (`acme-app`, `getacme`, `tryacme`, ...) when the input is taken everywhere.
- [ ] Optional WHOIS fallback for TLDs without an RDAP server.
- [ ] JSON output (`--json`) for scripting.
- [ ] Pre-baked TLD sets (`--preset startup`, `--preset web3`, ...).
- [ ] Persistent cache to avoid re-querying within a short window.

## Development

```bash
git clone https://github.com/yourname/domhunt
cd domhunt
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

## License

MIT — see [LICENSE](LICENSE).
