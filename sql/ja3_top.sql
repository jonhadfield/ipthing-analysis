-- Top JA3 ClientHello fingerprints by request count (hash only; no IP join).
SELECT
  ja3 AS fingerprint,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
WHERE ja3 IS NOT NULL AND btrim(ja3) <> ''
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15;
