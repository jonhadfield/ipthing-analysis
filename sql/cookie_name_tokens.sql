-- Anonymized cookie *name* token frequency (values are never stored).
-- High min-count only; no per-client cookie sets.
SELECT
  btrim(token) AS cookie_name,
  count(*)::bigint AS requests
FROM http_requests AS r,
LATERAL unnest(string_to_array(r.cookie_names, ',')) AS token
WHERE r.cookie_names IS NOT NULL
  AND btrim(r.cookie_names) <> ''
  AND btrim(token) <> ''
GROUP BY 1
HAVING count(*) >= 50
ORDER BY 2 DESC
LIMIT 20;
