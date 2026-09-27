# AGENTS.md

Analysis companion to the `ipthing` Go service. Read-only reporting over Neon Postgres.

## Rules

- Never write to the database from this project (SELECT only).
- Prefer a dedicated read-only Neon role; never commit `.env` or connection strings.
- Public report content must stay aggregated — no raw header dumps, IPs in tables of “top talkers” only at ASN/country grain unless explicitly requested.
- Never publish PTR hostnames, full User-Agents tied to clients, `tls_client_subject`, or per-client cookie name sets. JA3/JA4 hashes are frequency/cluster stats only.
- Keep narrative honest: this is traffic to a public IP echo service, not a representative sample of the whole internet.
- Do not modify the `ipthing` application repo unless the user asks.
