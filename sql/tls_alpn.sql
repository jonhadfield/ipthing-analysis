-- TLS ALPN negotiated protocol
SELECT
  CASE
    WHEN tls_negotiated_protocol IS NULL THEN '(unset)'
    WHEN btrim(tls_negotiated_protocol) = '' THEN '(empty)'
    ELSE tls_negotiated_protocol
  END AS alpn,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
