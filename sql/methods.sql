-- HTTP method mix (scanners often try odd verbs)
SELECT
  COALESCE(NULLIF(btrim(method), ''), '(empty)') AS method,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
