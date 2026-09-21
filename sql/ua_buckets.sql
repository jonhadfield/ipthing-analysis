-- Coarse User-Agent buckets (heuristic, not perfect detection)
SELECT
  CASE
    WHEN user_agent ILIKE 'curl/%' THEN 'curl'
    WHEN user_agent ILIKE 'wget%' THEN 'wget'
    WHEN user_agent ILIKE '%python-requests%'
      OR user_agent ILIKE '%Go-http-client%'
      OR user_agent ILIKE '%httpx%'
      OR user_agent ILIKE '%aiohttp%' THEN 'scripted HTTP clients'
    WHEN user_agent ILIKE '%bot%'
      OR user_agent ILIKE '%crawl%'
      OR user_agent ILIKE '%spider%'
      OR user_agent ILIKE '%slurp%'
      OR user_agent ILIKE '%censys%'
      OR user_agent ILIKE '%masscan%' THEN 'bot / scanner UA'
    WHEN user_agent ILIKE '%Mozilla%' THEN 'browser-like'
    WHEN user_agent IS NULL OR user_agent = '' THEN 'empty'
    ELSE 'other'
  END AS ua_bucket,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1
ORDER BY 2 DESC;
