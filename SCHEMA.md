# Schema reference (`http_requests` / `ip_info`)

Read-only view of the Neon tables used by this report. Source of truth for DDL is the
[`ipthing`](https://github.com/jonhadfield/ipthing) Go service migrations. This file
documents what the analysis project expects and what may appear on the public site.

## Deploy note (table owner)

If the app connects as a non-owner role, `CREATE TABLE IF NOT EXISTS` will not add
columns to an existing table, and `ALTER TABLE … ADD COLUMN` may be skipped for lack
of privilege. Run these as the table owner **before** shipping a binary that INSERTs
the new fields:

```sql
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS cookie_names TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS tls_did_resume BOOLEAN;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS tls_curve TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS tls_client_subject TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS ja3 TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS ja4 TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS ip_family TEXT;
ALTER TABLE http_requests ADD COLUMN IF NOT EXISTS ptr_hostname TEXT;
```

Older rows leave new columns NULL; report SQL treats NULL as “unknown / pre-feature.”

## `http_requests` columns

| Column | Type (Postgres) | Notes | Public report |
|--------|-----------------|-------|---------------|
| `id` | `SERIAL` | Primary key | not published |
| `ip` | `TEXT` | Client peer IP | ASN/country aggregates only; distinct-IP counts OK |
| `method`, `path`, `proto`, `scheme`, `host`, `request_uri` | `TEXT` | Request shape | aggregates / top-N paths & methods |
| `user_agent` | `TEXT` | Full UA string | coarse buckets only — never raw UA lists |
| `referer` | `TEXT` | Full referer URL | hostname only |
| `headers` | `TEXT` | Redacted header dump | **never** publish |
| `query_params` | `TEXT` | Query string / JSON | param **names** only |
| `timestamp` | `TIMESTAMP` | Request time | time series |
| `tls_version`, `tls_cipher_suite` | `INTEGER` | Wire values | mapped labels in charts |
| `tls_server_name`, `tls_negotiated_protocol` | `TEXT` | SNI / ALPN | aggregates |
| `tls_did_resume` | `BOOLEAN` | Session resumption | rate / share only |
| `tls_curve` | `TEXT` | Key exchange name (e.g. `X25519`) | top-N distribution |
| `tls_client_subject` | `TEXT` | mTLS client cert subject | **presence rate only** — never raw subjects |
| `ja3`, `ja4` | `TEXT` | ClientHello fingerprints | top hashes + shape clusters; no IP join |
| `ip_family` | `TEXT` | `ipv4` \| `ipv6` | family share (report may also derive from `ip`) |
| `ptr_hostname` | `TEXT` | Reverse DNS | **% with any PTR only** — never sample hostnames |
| `remote_addr`, `content_length`, `content_type`, `body` | mixed | body unused for persistence | latency/status aggregates |
| `has_cookies` | `BOOLEAN` | Cookie header present | rate in probe cards |
| `cookie_names` | `TEXT` | Comma-separated names; values never stored | optional high min-count token frequency |
| `claimed_xff`, `cf_connecting_ip` | `TEXT` | Spoofable forwarding headers | mismatch counts only |
| `duration_ms` | `BIGINT` | Handler duration | percentiles |
| `response_format`, `status_code` | text / int | Response outcome | distributions |

## `ip_info` columns

Geolocation cache keyed by `ip`: city, region, country, org, loc, etc. Public report
uses country and org aggregates only.

## Privacy rules for the public report

1. Never chart or list individual IPs, PTR hostnames, full User-Agents, raw headers,
   per-client cookie name sets, or `tls_client_subject` values.
2. Prefer distributions and top-N: address family, TLS version/cipher/curve, resume
   rate, HTTP proto, JA4/JA3 hash frequency.
3. JA3/JA4 narrative is frequency / uniqueness / coarse browser-vs-bot clusters —
   not “this fingerprint = this person.”
4. Tolerate NULL on newer columns (traffic before the feature landed).
5. Report builder skips queries whose required columns are absent so builds succeed
   before the owner migration is applied.
