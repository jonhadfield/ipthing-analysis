-- Top countries by distinct IPs seen
SELECT
  coalesce(nullif(country, ''), '(unknown)') AS country,
  count(*)::bigint AS ips
FROM ip_info
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
