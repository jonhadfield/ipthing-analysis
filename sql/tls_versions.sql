-- TLS versions present on recorded requests (numeric wire values)
SELECT
  CASE tls_version
    WHEN 772 THEN 'TLS 1.3'
    WHEN 771 THEN 'TLS 1.2'
    WHEN 770 THEN 'TLS 1.1'
    WHEN 769 THEN 'TLS 1.0'
    ELSE coalesce(tls_version::text, '(none/unknown)')
  END AS tls,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
