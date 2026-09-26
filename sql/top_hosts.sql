-- Top Host header values since Host recording resumed (2026-09-23 ~14:00 UTC).
SELECT
  coalesce(nullif(host, ''), '(empty)') AS host,
  count(*)::bigint AS requests
FROM http_requests
WHERE timestamp >= '2026-09-23 14:00'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
