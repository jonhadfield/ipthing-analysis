-- Networks seen over IPv6 (org / ASN grain only; loopback excluded).
-- IPv6 was enabled 2026-09-25; earlier IPv6 peer addresses are excluded as unreliable.
SELECT
  coalesce(nullif(i.org, ''), '(unknown)') AS org,
  count(DISTINCT r.ip)::bigint AS ips,
  count(*)::bigint AS requests
FROM http_requests AS r
LEFT JOIN ip_info AS i ON i.ip = r.ip
WHERE r.ip LIKE '%:%'
  AND r.ip NOT ILIKE '::ffff:%'
  AND r.ip <> '::1'
  AND r.timestamp >= '2026-09-25'
GROUP BY 1
ORDER BY 3 DESC, 2 DESC
LIMIT 15;
