-- How clients addressed the service: by name vs raw IP vs other/unknown.
-- Note: Host was not recorded 2025-12-19 through 2026-09-23.
SELECT
  CASE
    WHEN host ILIKE '%ipthing.net%'
      OR tls_server_name ILIKE '%ipthing.net%' THEN 'named (ipthing.net)'
    WHEN host ~ '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$' THEN 'raw IP (Host is address)'
    WHEN host IS NOT NULL AND host <> '' THEN 'other Host (wrong/spoofed name)'
    ELSE 'unknown (Host unset)'
  END AS access_mode,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
