-- Top Host header values (for the appendix table)
SELECT
  coalesce(nullif(host, ''), '(empty)') AS host,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
