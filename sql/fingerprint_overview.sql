-- Aggregate coverage / uniqueness for newer request metadata.
-- Never returns identifying values (no PTR hostnames, no mTLS subjects).
SELECT
  count(*)::bigint AS requests,
  count(*) FILTER (
    WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
  )::bigint AS with_ja4,
  count(DISTINCT ja4) FILTER (
    WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
  )::bigint AS distinct_ja4,
  count(*) FILTER (
    WHERE ja3 IS NOT NULL AND btrim(ja3) <> ''
  )::bigint AS with_ja3,
  count(DISTINCT ja3) FILTER (
    WHERE ja3 IS NOT NULL AND btrim(ja3) <> ''
  )::bigint AS distinct_ja3,
  count(*) FILTER (
    WHERE ptr_hostname IS NOT NULL AND btrim(ptr_hostname) <> ''
  )::bigint AS with_ptr,
  count(*) FILTER (
    WHERE tls_client_subject IS NOT NULL AND btrim(tls_client_subject) <> ''
  )::bigint AS with_mtls_subject,
  count(*) FILTER (WHERE tls_did_resume IS NOT NULL)::bigint AS with_resume_flag,
  count(*) FILTER (WHERE tls_did_resume IS TRUE)::bigint AS resumed,
  count(*) FILTER (
    WHERE tls_curve IS NOT NULL AND btrim(tls_curve) <> ''
  )::bigint AS with_tls_curve,
  count(*) FILTER (WHERE COALESCE(has_cookies, false))::bigint AS with_cookies
FROM http_requests;
