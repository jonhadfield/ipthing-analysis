-- Presence rate only — never returns tls_client_subject values.
SELECT
  count(*) FILTER (
    WHERE tls_client_subject IS NOT NULL AND btrim(tls_client_subject) <> ''
  )::bigint AS with_mtls_subject
FROM http_requests;
