-- Top query-string parameter *names* (not values) — probe / exploit fingerprints
-- Strip illegal JSON \u0000 escapes some scanners inject before parsing.
SELECT
  key AS param_key,
  count(*)::bigint AS requests
FROM http_requests h
CROSS JOIN LATERAL json_object_keys(
  replace(h.query_params, E'\\u0000', '')::json
) AS key
WHERE h.query_params IS NOT NULL
  AND btrim(h.query_params) NOT IN ('', '{}', 'null')
  AND left(btrim(h.query_params), 1) = '{'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 25;
