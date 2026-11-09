-- JA3 coverage / uniqueness only (hash aggregates — never joined to IPs here).
SELECT
  count(*) FILTER (
    WHERE ja3 IS NOT NULL AND btrim(ja3) <> ''
  )::bigint AS with_ja3,
  count(DISTINCT ja3) FILTER (
    WHERE ja3 IS NOT NULL AND btrim(ja3) <> ''
  )::bigint AS distinct_ja3
FROM http_requests;
