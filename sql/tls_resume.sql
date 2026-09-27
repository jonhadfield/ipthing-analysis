-- TLS session resumption rate among rows where the flag is known.
-- Older rows leave tls_did_resume NULL; those are excluded from the rate.
SELECT
  count(*) FILTER (WHERE tls_did_resume IS NOT NULL)::bigint AS with_resume_flag,
  count(*) FILTER (WHERE tls_did_resume IS TRUE)::bigint AS resumed,
  count(*) FILTER (WHERE tls_did_resume IS FALSE)::bigint AS full_handshake,
  round(
    100.0 * count(*) FILTER (WHERE tls_did_resume IS TRUE)
      / nullif(count(*) FILTER (WHERE tls_did_resume IS NOT NULL), 0),
    1
  ) AS resume_pct
FROM http_requests;
