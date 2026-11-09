"""DB-free smoke tests for the public report template."""

from __future__ import annotations

from ipthing_analysis.build import render_report

_CHART = "<!--chart-->"


def _charts() -> dict[str, str]:
    keys = [
        "daily",
        "access",
        "access_daily",
        "countries",
        "orgs",
        "tls",
        "proto",
        "tls_ciphers",
        "tls_alpn",
        "ua",
        "ua_mobile",
        "ua_daily",
        "methods",
        "paths",
        "path_themes",
        "probe_paths_daily",
        "query_keys",
        "host_sni",
        "status",
        "formats",
        "referers",
        "ip_family",
        "ipv6_share",
        "heatmap",
        "tls_curves",
        "tls_resume",
        "ja4_top",
        "ja3_top",
        "ja4_shape",
        "cookie_names",
    ]
    return {key: _CHART for key in keys}


def _context() -> dict[str, object]:
    return {
        "generated_at": "2026-11-08 12:00 UTC",
        "overview": {
            "requests": 1000,
            "unique_ips": 100,
            "first_day": "2025-07-26",
            "last_day": "2026-11-08",
            "https_requests": 900,
            "http_requests": 100,
        },
        "probe": {
            "with_query_params": 1,
            "distinct_methods": 2,
            "distinct_paths": 3,
            "non_root_requests": 4,
            "status_404": 5,
            "with_claimed_xff": 6,
            "with_cf_connecting_ip": 7,
            "xff_differs_from_peer": 8,
            "cf_differs_from_peer": 9,
            "with_cookies": 10,
        },
        "latency": {
            "with_duration": 10,
            "p50_ms": "1",
            "p95_ms": "2",
            "p99_ms": "3",
        },
        "ipv6": {
            "requests": 1,
            "unique_ips": 1,
            "share_pct": "1.0%",
            "first_day": "2026-09-25",
        },
        "ip_family": [],
        "ipv6_orgs": [],
        "referer_overview": {"with_referer": 1, "without_referer": 2},
        "countries": [],
        "orgs": [],
        "access": [],
        "top_hosts": [],
        "methods": [],
        "paths": [],
        "path_themes": [],
        "query_keys": [],
        "host_sni": [],
        "status_codes": [],
        "response_formats": [],
        "tls_ciphers": [],
        "tls_curves": [],
        "fingerprint": {
            "with_ja4": 0,
            "distinct_ja4": 0,
            "ja4_coverage": "—",
            "with_ja3": 0,
            "distinct_ja3": 0,
            "ptr_rate": "—",
            "mtls_rate": "—",
            "resume_pct": "—",
            "with_resume_flag": 0,
            "columns_ready": True,
        },
        "ja4_top": [],
        "ja3_top": [],
        "ja4_shape": [],
        "cookie_name_tokens": [],
        "referer_hosts": [],
        "ua": [
            {
                "ua_bucket": "curl",
                "requests": 600,
                "share_pct": 60.0,
                "unique_ips": 40,
            }
        ],
        "ua_summary": {
            "top_bucket": "curl",
            "top_requests": 600,
            "top_unique_ips": 40,
            "top_share_pct": "60.0%",
            "distinct_buckets": 1,
            "total_requests": 600,
        },
        "charts": _charts(),
    }


def test_render_report_includes_seo_basics() -> None:
    html = render_report(**_context())
    assert "What hits a public IP echo service? · ipthing stats" in html
    assert 'rel="canonical" href="https://stats.ipthing.net/"' in html
    assert "Live traffic analysis of ipthing.net: 1,000 requests from 100 IPs" in html
    assert 'content="https://stats.ipthing.net/og-share.jpg"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html
    assert '"@type": "Dataset"' in html


def test_render_report_marks_notes_nosnippet() -> None:
    html = render_report(**_context())
    assert 'class="note" data-nosnippet>' in html
    assert "ipthing trusts the TCP peer address" in html


def test_render_report_highlights_top_ua_class() -> None:
    html = render_report(**_context())
    assert "Most common class" in html
    assert "curl" in html
    assert "60.0%" in html
    assert "Raw UA text is never listed here" in html


def test_render_report_includes_access_daily_section() -> None:
    html = render_report(**_context())
    assert "{{ charts.access_daily" not in html
    assert html.count(_CHART) >= 20
    assert "internet-wide scanning rather than people typing the hostname" in html


def test_render_report_includes_ua_daily_chart() -> None:
    html = render_report(**_context())
    assert "{{ charts.ua_daily" not in html
    assert html.count(_CHART) >= 21
    assert "Client flavour (User-Agent heuristics)" in html
