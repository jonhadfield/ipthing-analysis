-- Top request paths (bucket noise; do not expand into full request URIs)
SELECT
  COALESCE(NULLIF(btrim(path), ''), '(empty)') AS path,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
