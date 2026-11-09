-- Always-safe request totals for fingerprint / TLS presence cards.
-- Optional JA3/JA4/PTR/mTLS counts are loaded separately in build.py so a
-- missing column does not zero out the whole overview.
SELECT
  count(*)::bigint AS requests,
  count(*) FILTER (WHERE COALESCE(has_cookies, false))::bigint AS with_cookies
FROM http_requests;
