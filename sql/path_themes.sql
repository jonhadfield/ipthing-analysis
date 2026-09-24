-- Coarse themes for non-root paths (404 / scanner targets)
SELECT
  CASE
    WHEN path ILIKE '%/.env%'
      OR path ILIKE '%.env'
      OR path ILIKE '%/credentials%'
      OR path ILIKE '%/secrets%'
      OR path ILIKE '%id_rsa%' THEN 'secrets / .env'
    WHEN path ILIKE '%wp-%'
      OR path ILIKE '%wordpress%'
      OR path ILIKE '%/wp/'
      OR path ILIKE '%xmlrpc.php%'
      OR path ILIKE '%/wp-admin%'
      OR path ILIKE '%/wp-content%' THEN 'WordPress'
    WHEN path ILIKE '%.git%'
      OR path ILIKE '%/.svn%'
      OR path ILIKE '%/.hg%' THEN 'VCS metadata'
    WHEN path ILIKE '%phpunit%'
      OR path ILIKE '%phpinfo%'
      OR path ILIKE '%.php%' THEN 'PHP probes'
    WHEN path ILIKE '%admin%'
      OR path ILIKE '%login%'
      OR path ILIKE '%signin%'
      OR path ILIKE '%/console%' THEN 'admin / login'
    WHEN path ILIKE '%actuator%'
      OR path ILIKE '%/api/%'
      OR path ILIKE '%swagger%'
      OR path ILIKE '%graphql%' THEN 'API / actuator'
    WHEN path ILIKE '%backup%'
      OR path ILIKE '%.sql%'
      OR path ILIKE '%.bak%'
      OR path ILIKE '%.zip%'
      OR path ILIKE '%.tar%' THEN 'backups / dumps'
    WHEN path ILIKE '%docker%'
      OR path ILIKE '%kubernetes%'
      OR path ILIKE '%/server-status%'
      OR path ILIKE '%/server-info%' THEN 'infra / debug'
    ELSE 'other'
  END AS path_theme,
  count(*)::bigint AS requests,
  count(DISTINCT ip)::bigint AS unique_ips
FROM http_requests
WHERE path IS DISTINCT FROM '/'
  AND btrim(COALESCE(path, '')) <> ''
GROUP BY 1
ORDER BY 2 DESC;
