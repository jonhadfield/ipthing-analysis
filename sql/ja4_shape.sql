-- Coarse JA4 shape buckets for narrative (browser-like vs bot-like clusters).
-- Heuristic only: JA4 encodes TLS version, SNI presence, and ALPN in the first
-- segment (e.g. t13d1516h2_…). Not identity; not a security product.
SELECT
  shape,
  count(*)::bigint AS requests,
  count(DISTINCT ja4)::bigint AS distinct_ja4
FROM (
  SELECT
    ja4,
    CASE
      WHEN ja4 ~* '^t13d[0-9]{4}h[23]' THEN 'browser-like (TLS1.3 + SNI + h2/h3)'
      WHEN ja4 ~* '^t12d[0-9]{4}h[12]' THEN 'legacy-browser-like (TLS1.2 + SNI)'
      WHEN ja4 ~* '^t1[23]i' THEN 'no-SNI / IP-SNI (often scanners)'
      WHEN ja4 ~* '^t1[23]d[0-9]{4}(00|h0)' THEN 'empty/odd ALPN'
      WHEN ja4 ~* '^q' THEN 'QUIC / HTTP3-shaped'
      ELSE 'other / uncommon'
    END AS shape
  FROM http_requests
  WHERE ja4 IS NOT NULL AND btrim(ja4) <> ''
) AS classified
GROUP BY 1
ORDER BY 2 DESC;
