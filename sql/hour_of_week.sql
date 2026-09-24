-- Request volume by ISO day-of-week (1=Mon … 7=Sun) and hour (UTC)
SELECT
  extract(isodow FROM timestamp)::int AS dow,
  extract(hour FROM timestamp)::int AS hour,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1, 2
ORDER BY 1, 2;
