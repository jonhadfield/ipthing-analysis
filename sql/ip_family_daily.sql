-- Daily IPv4 vs IPv6 request counts (loopback excluded).
-- IPv6 was enabled 2026-09-25; earlier IPv6 peer addresses are excluded as unreliable.
SELECT
  timestamp::date AS day,
  count(*) FILTER (WHERE NOT is_v6)::bigint AS ipv4_requests,
  count(*) FILTER (WHERE is_v6)::bigint AS ipv6_requests
FROM (
  SELECT
    timestamp,
    ip LIKE '%:%' AND ip NOT ILIKE '::ffff:%' AS is_v6
  FROM http_requests
  WHERE ip <> '::1' AND ip NOT LIKE '127.%' AND ip NOT LIKE '::ffff:127.%'
    AND NOT (ip LIKE '%:%' AND ip NOT ILIKE '::ffff:%' AND ip <> '::1' AND timestamp < '2026-09-25')
) AS classified
GROUP BY 1
ORDER BY 1;
