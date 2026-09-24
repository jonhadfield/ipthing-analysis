-- Relationship between HTTP Host and TLS SNI (opportunistic TLS / probe signal).
-- Note: Host was not recorded 2025-12-19 through 2026-09-23.
SELECT
  CASE
    WHEN host_norm IS NOT NULL AND sni_norm IS NOT NULL AND host_norm = sni_norm
      THEN 'Host and SNI agree'
    WHEN host_norm IS NOT NULL AND sni_norm IS NOT NULL AND host_norm <> sni_norm
      THEN 'Host / SNI mismatch'
    WHEN host_norm IS NOT NULL AND sni_norm IS NULL
      THEN 'Host set, SNI empty'
    WHEN host_norm IS NULL AND sni_norm IS NOT NULL
      THEN 'SNI set, Host empty'
    ELSE 'both empty'
  END AS host_sni_relation,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM (
  SELECT
    ip,
    NULLIF(lower(split_part(COALESCE(host, ''), ':', 1)), '') AS host_norm,
    NULLIF(lower(COALESCE(tls_server_name, '')), '') AS sni_norm
  FROM http_requests
) AS normalized
GROUP BY 1
ORDER BY 2 DESC;
