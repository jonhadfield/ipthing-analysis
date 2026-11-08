-- Daily named vs raw-IP vs other access mix.
-- Limited to rows since Host recording resumed (2026-09-23 ~14:00 UTC);
-- Host was not recorded from 2025-12-19 until then.
SELECT
  timestamp::date AS day,
  CASE
    WHEN host ILIKE '%ipthing.net%'
      OR tls_server_name ILIKE '%ipthing.net%' THEN 'named (ipthing.net)'
    WHEN host ~ '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$'
      OR host ~ '^\[[0-9A-Fa-f:.]+\](:[0-9]+)?$' THEN 'raw IP (Host is address)'
    WHEN host IS NOT NULL AND host <> '' THEN 'other Host (wrong/spoofed name)'
    ELSE 'unknown (Host unset)'
  END AS access_mode,
  count(*)::bigint AS requests
FROM http_requests
WHERE timestamp >= '2026-09-23 14:00'
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
