-- Top JA4 ClientHello fingerprints by request count (hash only; no IP join).
SELECT
  ja4 AS fingerprint,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;
