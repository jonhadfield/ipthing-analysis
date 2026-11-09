-- Daily coarse User-Agent class mix (same heuristics as ua_buckets.sql).
-- Public report uses these labels only — never raw User-Agent strings.
SELECT
  timestamp::date AS day,
  CASE
    WHEN user_agent IS NULL OR user_agent = '' THEN 'empty'
    WHEN user_agent ILIKE 'curl/%' THEN 'curl'
    WHEN user_agent ILIKE 'wget%' THEN 'wget'
    WHEN user_agent ILIKE '%python-requests%'
      OR user_agent ILIKE '%httpx%'
      OR user_agent ILIKE '%aiohttp%' THEN 'Python HTTP clients'
    WHEN user_agent ILIKE '%Go-http-client%' THEN 'Go HTTP client'
    WHEN user_agent ILIKE '%bot%'
      OR user_agent ILIKE '%crawl%'
      OR user_agent ILIKE '%spider%'
      OR user_agent ILIKE '%slurp%'
      OR user_agent ILIKE '%censys%'
      OR user_agent ILIKE '%masscan%'
      OR user_agent ILIKE '%zgrab%'
      OR user_agent ILIKE '%nuclei%'
      OR user_agent ILIKE '%Shodan%'
      OR user_agent ILIKE '%zmap%'
      OR user_agent ILIKE 'l9tcpid/%'
      OR user_agent ILIKE 'l9explore/%'
      OR user_agent ILIKE '%fasthttp%'
      OR user_agent ILIKE '%Palo Alto Networks%'
      OR user_agent ILIKE 'libredtail-http%'
      OR user_agent ILIKE '%odin-scanner%'
      OR user_agent ILIKE '%Banner Detection%'
      OR user_agent ILIKE 'Uptimeflare%'
      OR user_agent ILIKE '%Uptimeflare%' THEN 'bot / scanner UA'
    WHEN user_agent ILIKE '%Edg/%' OR user_agent ILIKE '%EdgA/%' THEN 'Edge-like'
    WHEN user_agent ILIKE '%Firefox/%' OR user_agent ILIKE '%FxiOS/%' THEN 'Firefox-like'
    WHEN user_agent ILIKE '%Chrome/%'
      AND user_agent NOT ILIKE '%Edg/%'
      AND user_agent NOT ILIKE '%OPR/%' THEN 'Chrome-like'
    WHEN user_agent ILIKE '%CriOS/%' THEN 'Chrome-like'
    WHEN user_agent ILIKE '%Safari/%'
      AND user_agent NOT ILIKE '%Chrome/%'
      AND user_agent NOT ILIKE '%Chromium/%'
      AND user_agent NOT ILIKE '%CriOS/%' THEN 'Safari-like'
    WHEN user_agent ILIKE '%OPR/%' OR user_agent ILIKE '%Opera%' THEN 'Opera-like'
    WHEN user_agent ILIKE '%Mozilla%' THEN 'other browser-like'
    ELSE 'other'
  END AS ua_bucket,
  count(*)::bigint AS requests
FROM http_requests
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
