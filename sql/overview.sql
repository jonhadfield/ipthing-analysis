-- Overview stats for the dataset
SELECT
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips,
  min(timestamp)::date AS first_day,
  max(timestamp)::date AS last_day,
  count(*) FILTER (WHERE scheme = 'https')::bigint AS https_requests,
  count(*) FILTER (WHERE scheme = 'http')::bigint AS http_requests
FROM http_requests;
