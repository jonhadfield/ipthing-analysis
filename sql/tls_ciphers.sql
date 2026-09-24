-- TLS cipher suite IDs (uint16). Names are resolved in the report builder.
SELECT
  tls_cipher_suite AS cipher_id,
  count(*)::bigint AS requests
FROM http_requests
WHERE tls_cipher_suite IS NOT NULL
  AND tls_cipher_suite <> 0
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
