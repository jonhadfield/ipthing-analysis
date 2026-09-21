-- Daily request volume
SELECT
  timestamp::date AS day,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 1;
