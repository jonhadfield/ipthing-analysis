-- HTTP method mix since non-GET methods were allowed (2026-09-23).
-- Earlier rows are GET-only by construction, so they would swamp other verbs.
SELECT
  COALESCE(NULLIF(btrim(method), ''), '(empty)') AS method,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips,
  round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS share_pct
FROM http_requests
WHERE timestamp >= '2026-09-23'
GROUP BY 1
ORDER BY 2 DESC;
