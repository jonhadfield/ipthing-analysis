-- Security-oriented request-shape totals (aggregates only)
SELECT
  count(*)::bigint AS requests,
  count(DISTINCT method)::bigint AS distinct_methods,
  count(DISTINCT path)::bigint AS distinct_paths,
  count(*) FILTER (
    WHERE path IS DISTINCT FROM '/'
      AND btrim(COALESCE(path, '')) <> ''
  )::bigint AS non_root_requests,
  count(*) FILTER (
    WHERE status_code = 404
  )::bigint AS status_404,
  count(*) FILTER (
    WHERE query_params IS NOT NULL
      AND btrim(query_params) NOT IN ('', '{}', 'null')
  )::bigint AS with_query_params,
  count(*) FILTER (
    WHERE claimed_xff IS NOT NULL AND btrim(claimed_xff) <> ''
  )::bigint AS with_claimed_xff,
  count(*) FILTER (
    WHERE cf_connecting_ip IS NOT NULL AND btrim(cf_connecting_ip) <> ''
  )::bigint AS with_cf_connecting_ip,
  count(*) FILTER (
    WHERE claimed_xff IS NOT NULL
      AND btrim(claimed_xff) <> ''
      AND btrim(split_part(claimed_xff, ',', 1)) <> ip
  )::bigint AS xff_differs_from_peer,
  count(*) FILTER (
    WHERE cf_connecting_ip IS NOT NULL
      AND btrim(cf_connecting_ip) <> ''
      AND btrim(cf_connecting_ip) <> ip
  )::bigint AS cf_differs_from_peer,
  count(*) FILTER (WHERE COALESCE(has_cookies, false))::bigint AS with_cookies
FROM http_requests;
