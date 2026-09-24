-- HTTP status mix (NULL = older rows before status_code was logged)
SELECT
  CASE
    WHEN status_code IS NULL THEN '(unset / older rows)'
    ELSE status_code::text
  END AS status,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
