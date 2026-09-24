-- Referer presence summary
SELECT
  count(*)::bigint AS requests,
  count(*) FILTER (
    WHERE referer IS NOT NULL AND btrim(referer) <> ''
  )::bigint AS with_referer,
  count(*) FILTER (
    WHERE referer IS NULL OR btrim(referer) = ''
  )::bigint AS without_referer
FROM http_requests;
