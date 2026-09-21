-- Top network operators (AS orgs) by distinct IPs
SELECT
  coalesce(nullif(left(org, 80), ''), '(unknown)') AS org,
  count(*)::bigint AS ips
FROM ip_info
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
