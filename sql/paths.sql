-- Top non-root request paths (404 / probe targets). Bare "/" is excluded so
-- scanner paths are visible; almost all successful inspector traffic is "/".
SELECT
  COALESCE(NULLIF(btrim(path), ''), '(empty)') AS path,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
WHERE path IS DISTINCT FROM '/'
  AND btrim(COALESCE(path, '')) <> ''
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
