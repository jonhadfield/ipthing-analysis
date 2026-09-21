-- Daily mix of named vs raw-IP access (excludes empty Host for clarity of trend)
SELECT
  timestamp::date AS day,
  count(*) FILTER (
    WHERE host ILIKE '%ipthing.net%' OR tls_server_name ILIKE '%ipthing.net%'
  )::bigint AS named_requests,
  count(*) FILTER (
    WHERE host ~ '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$'
  )::bigint AS raw_ip_requests,
  count(*) FILTER (
    WHERE (host IS NULL OR host = '')
      AND (tls_server_name IS NULL OR tls_server_name = '')
  )::bigint AS unset_requests,
  count(*) FILTER (
    WHERE host IS NOT NULL AND host <> ''
      AND host NOT ILIKE '%ipthing.net%'
      AND host !~ '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$'
      AND coalesce(tls_server_name, '') NOT ILIKE '%ipthing.net%'
  )::bigint AS other_host_requests
FROM http_requests
GROUP BY 1
ORDER BY 1;
