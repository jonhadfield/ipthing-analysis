-- HTTP protocol versions
SELECT
  coalesce(nullif(proto, ''), '(unset)') AS proto,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
