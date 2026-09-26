# ipthing-analysis

Static analysis of traffic recorded by [ipthing](https://github.com/jonhadfield/ipthing) — a public HTTP request inspector at [ipthing.net](https://ipthing.net).

**Live report:** [stats.ipthing.net](https://stats.ipthing.net/)

## What this is

A **separate** repo from the Go service. It reads the Postgres database (Neon) in **read-only** fashion and builds a static HTML report: charts, tables, and short explanations of what the data shows.

The production app keeps writing request logs; this project only interprets them.

## Dataset (high level)

| Fact | Meaning |
|------|---------|
| Source | `http_requests` + `ip_info` in the `ipthing` Neon database |
| Shape | Mostly `GET /` (only `GET` was allowed until 23 Sep 2026) — people and bots probing “what is my IP / headers” |
| Useful dimensions | Time, IP/ASN/country (geo cache), TLS version, HTTP proto, User-Agent class, spoofed forwarding headers; `Host` was not recorded 19 Dec 2025–23 Sep 2026 |
| Exclusions | IPv6 was only enabled on 25 Sep 2026. IPv6 client addresses logged before then are unreliable and are excluded from every figure: `build.py` prefixes each query with CTEs that shadow `http_requests` and `ip_info` (cut-off set by `IPV6_ENABLED`). Loopback `::1` and IPv4-mapped `::ffff:` addresses are kept |

Privacy: public pages use **aggregates only**. Cookie/Authorization values are not stored by the app (redacted at write time). Do not publish raw `headers` blobs or individual client identifiers in the site.

## Quick start

```bash
cp .env.example .env
# set DATABASE_URL to a read-only Neon URL for database "ipthing"

uv sync
uv run ipthing-report
open docs/index.html
```

## Layout

```
sql/           # named queries used by the report
src/           # report builder
templates/     # HTML shell + narrative
static/        # favicon, apple-touch-icon, web manifest
docs/          # generated static output (commit or publish via Pages)
```

## Publishing

The public report is at **[https://stats.ipthing.net/](https://stats.ipthing.net/)** (GitHub Pages behind that hostname).

GitHub Actions rebuilds the report **daily** (06:00 UTC) and on each push that changes queries/templates/code, then deploys via GitHub Pages.

1. Add a repository secret `DATABASE_URL` — the same read-only Neon URL as in `.env`.
2. In **Settings → Pages**, set Source to **GitHub Actions** (not “Deploy from a branch”).
3. Run **Actions → Update report → Run workflow** once to publish.

Local `docs/index.html` is still useful for preview (`make open`); production always comes from the workflow. To run weekly instead of daily, change the cron in `.github/workflows/update-report.yml` to `0 6 * * 1`.
