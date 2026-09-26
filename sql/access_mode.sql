-- How clients addressed the service: by name vs raw IP vs other/unknown.
-- Limited to rows since Host recording resumed (2026-09-23 ~14:00 UTC);
-- Host was not recorded from 2025-12-19 until then.
SELECT
  CASE
    WHEN host ILIKE '%ipthing.net%'
      OR tls_server_name ILIKE '%ipthing.net%' THEN 'named (ipthing.net)'
    WHEN host ~ '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$'
      OR host ~ '^\[[0-9A-Fa-f:.]+\](:[0-9]+)?$' THEN 'raw IP (Host is address)'
    WHEN host IS NOT NULL AND host <> '' THEN 'other Host (wrong/spoofed name)'
    ELSE 'unknown (Host unset)'
  END AS access_mode,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
WHERE timestamp >= '2026-09-23 14:00'
GROUP BY 1
ORDER BY 2 DESC;
