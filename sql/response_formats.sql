-- Response format chosen by the service (browser HTML vs JSON clients vs errors)
SELECT
  CASE
    WHEN response_format IS NULL OR btrim(response_format) = '' THEN '(unset / older rows)'
    ELSE response_format
  END AS response_format,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
