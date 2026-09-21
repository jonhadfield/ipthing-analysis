# ipthing-analysis

Static analysis of traffic recorded by [ipthing](https://github.com/jonhadfield/ipthing) — a public HTTP request inspector at [ipthing.net](https://ipthing.net).

## What this is

A **separate** repo from the Go service. It reads the Postgres database (Neon) in **read-only** fashion and builds a static HTML report: charts, tables, and short explanations of what the data shows.

The production app keeps writing request logs; this project only interprets them.

## Dataset (high level)

| Fact | Meaning |
|------|---------|
| Source | `http_requests` + `ip_info` in the `ipthing` Neon database |
| Shape | Almost entirely `GET /` — people and bots probing “what is my IP / headers” |
| Useful dimensions | Time, IP/ASN/country (geo cache), TLS version, HTTP proto, User-Agent class, spoofed forwarding headers |

Privacy: public pages use **aggregates only**. Cookie/Authorization values are not stored by the app (redacted at write time). Do not publish raw `headers` blobs or individual client identifiers in the site.

## Quick start

```bash
cp .env.example .env
# set DATABASE_URL to a read-only Neon URL for database "ipthing"

uv sync
uv run ipthing-report
open site/index.html
```

## Layout

```
sql/           # named queries used by the report
src/           # report builder
templates/     # HTML shell + narrative
site/          # generated static output (commit or publish via Pages)
```

## Publishing

`site/` is static. Point GitHub Pages (or Cloudflare Pages) at `/site`, or rebuild in CI on a schedule.
