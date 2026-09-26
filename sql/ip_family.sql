-- Requests by client address family. IPv4-mapped IPv6 (::ffff:a.b.c.d) counts as IPv4;
-- loopback (::1, 127.0.0.0/8) is local testing and kept separate.
-- IPv6 was enabled 2026-09-25; earlier IPv6 peer addresses are excluded as unreliable.
SELECT
  family,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips,
  min(timestamp)::date AS first_day,
  max(timestamp)::date AS last_day
FROM (
  SELECT
    ip,
    timestamp,
    CASE
      WHEN ip = '::1' OR ip LIKE '127.%' OR ip LIKE '::ffff:127.%' THEN 'loopback'
      WHEN ip LIKE '%:%' AND ip NOT ILIKE '::ffff:%' THEN 'IPv6'
      ELSE 'IPv4'
    END AS family
  FROM http_requests
  WHERE NOT (ip LIKE '%:%' AND ip NOT ILIKE '::ffff:%' AND ip <> '::1' AND timestamp < '2026-09-25')
) AS classified
GROUP BY 1
ORDER BY 2 DESC;
