-- Referer presence + top referer hosts (hostname only; no full URLs in the public report)
SELECT
  CASE
    WHEN referer IS NULL OR btrim(referer) = '' THEN '(none)'
    WHEN substring(referer FROM 'https?://([^/]+)') IS NOT NULL
      THEN lower(substring(referer FROM 'https?://([^/]+)'))
    ELSE '(opaque / non-http)'
  END AS referer_host,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC
LIMIT 25;
