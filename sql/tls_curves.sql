-- Negotiated TLS key-exchange curve names (aggregate only).
-- Older rows / plain HTTP leave tls_curve NULL.
SELECT
  coalesce(nullif(btrim(tls_curve), ''), '(unset)') AS curve,
  count(*)::bigint AS requests
FROM http_requests
WHERE scheme = 'https'
  OR tls_version IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
