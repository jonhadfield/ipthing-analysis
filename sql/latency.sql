-- Latency percentiles (ms) where duration was recorded
SELECT
  count(*)::bigint AS with_duration,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_ms
FROM http_requests
WHERE duration_ms IS NOT NULL
  AND duration_ms >= 0;
