# domhunt

> Check domain name availability across many TLDs in one search — from your **browser** or your **terminal**.

You have a project name in mind. You want to know if `acme.com`, `acme.io`,
`acme.dev`, `acme.app`, `acme.ai`, ... are taken. Opening Namecheap or GoDaddy
and typing each one is slow. `domhunt` does it in one go.

## Two ways to use it

### 1. Browser — no install, no signup, no server

Live demo: **https://syntaxixr.github.io/domhunt/**

The web UI is a single static HTML file. It calls `rdap.org` directly from
your browser (CORS-enabled). No backend required — hosted free on **GitHub
Pages** with auto-deploy on every push.

### 2. Terminal (one line)

```bash
pip install domhunt
domhunt acme
```

```text
           domhunt: 'acme'
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
- This is just a tiny CLI **and** a single-page web UI — one query, one table, done.

## CLI usage

```bash
# Default curated TLD set (12 developer-friendly TLDs)
domhunt myproject

# Custom list
domhunt acme --tlds com,io,dev,app

# Extended set (~30 TLDs)
domhunt acme --tlds all

# Only print the ones that are available (useful in scripts)
domhunt newco --tlds all --available-only
```

| Flag                   | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `--tlds`               | Comma-separated TLDs, or `all` for extended list. |
| `-c, --concurrency`    | Max parallel RDAP queries (default `10`).         |
| `-a, --available-only` | Hide taken/unknown domains.                       |
| `-h, --help`           | Show help.                                        |
| `--version`            | Show version.                                     |

## Web UI

Run the web app locally:

```bash
pip install domhunt
domhunt-web
# -> open http://localhost:8000
```

Or hit the JSON API directly:

```bash
curl "http://localhost:8000/api/check?name=acme&tlds=com,io,dev"
```

```json
{
  "name": "acme",
  "results": [
    { "domain": "acme.com", "status": "taken", "detail": "" },
    { "domain": "acme.io",  "status": "taken", "detail": "" },
    { "domain": "acme.dev", "status": "available", "detail": "" }
  ]
}
```

## Deploy your own (free)

### GitHub Pages — **recommended, $0 forever, no server**

The site in `docs/` is a single self-contained HTML file. It calls
`https://rdap.org/` directly from the browser (rdap.org sends
`Access-Control-Allow-Origin: *`, so no proxy is needed). That means:

- **No backend.** No server to pay for, no cold starts.
- **Auto-deploys** on every push via `.github/workflows/pages.yml`.

Setup (one time):

1. Push this repo to your GitHub.
2. Go to **Settings → Pages** in your repo.
3. Set **Source** to **GitHub Actions**.
4. Push to `main`. The workflow publishes `docs/` and prints the URL.

Your site lives at `https://YOURNAME.github.io/domhunt/`.

### Render — if you want the Python backend version

The FastAPI app under `src/domhunt/web.py` is included for self-hosters who
want to add caching, rate-limiting, or auth in front of RDAP.

1. Push to GitHub.
2. On <https://render.com>: **New +** → **Blueprint** → pick your repo.
3. Render reads `render.yaml` and provisions a free web service.

### Docker (anywhere)

```bash
docker build -t domhunt .
docker run -p 8000:8000 domhunt
```

Works on Fly.io, Railway, your VPS, etc.

## How it works

`domhunt` queries the public [RDAP](https://datatracker.ietf.org/doc/html/rfc7480)
gateway at <https://rdap.org/>. RDAP is the modern successor to WHOIS (defined
by ICANN, adopted by all major registries) and returns clean JSON over HTTPS:

- HTTP `404` → domain is **available**
- HTTP `200` → domain is **taken**
- HTTP `400` → that TLD doesn't expose an RDAP server (rare; surfaced as `unknown`)

Checks run concurrently with `asyncio` + `httpx`, so 30 TLDs take a couple of
seconds, not 30.

## Project layout

```
domhunt/
├── src/domhunt/
│   ├── cli.py           # Click-based CLI
│   ├── checker.py       # async RDAP queries (the brain)
│   ├── tlds.py          # curated TLD lists
│   ├── web.py           # FastAPI app for the web UI / JSON API
│   └── static/index.html
├── tests/               # pytest + respx + FastAPI TestClient (16 tests)
├── .github/workflows/   # CI on Python 3.10 / 3.11 / 3.12
├── Dockerfile           # for any container host
└── render.yaml          # one-click deploy on Render
```


## Development

```bash
git clone https://github.com/syntaxixr/domhunt
cd domhunt
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                # 16 tests
ruff check .
domhunt acme                          # try the CLI
domhunt-web                           # try the web UI on :8000
```

## License

MIT — see [LICENSE](LICENSE).
