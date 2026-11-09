-- JA4 coverage / uniqueness only (hash aggregates — never joined to IPs here).
SELECT
  count(*) FILTER (
    WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
  )::bigint AS with_ja4,
  count(DISTINCT ja4) FILTER (
    WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
  )::bigint AS distinct_ja4
FROM http_requests;
