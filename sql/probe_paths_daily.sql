-- Daily mix of successful root traffic vs non-root / 404 probes
SELECT
  timestamp::date AS day,
  count(*) FILTER (
    WHERE path = '/'
      AND (status_code IS NULL OR status_code = 200)
  )::bigint AS root_ok,
  count(*) FILTER (
    WHERE status_code = 404
      OR (
        path IS DISTINCT FROM '/'
        AND btrim(COALESCE(path, '')) <> ''
      )
  )::bigint AS probe_or_404,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 1;
