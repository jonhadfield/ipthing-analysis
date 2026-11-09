-- Presence rate only — never returns PTR hostname values.
SELECT
  count(*) FILTER (
    WHERE ptr_hostname IS NOT NULL AND btrim(ptr_hostname) <> ''
  )::bigint AS with_ptr
FROM http_requests;
