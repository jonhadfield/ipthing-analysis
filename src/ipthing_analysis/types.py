"""Typed shapes for report aggregates (documentation + editor help)."""

from __future__ import annotations

from typing import TypedDict


class OverviewRow(TypedDict):
    requests: int
    unique_ips: int
    first_day: object
    last_day: object
    https_requests: int
    http_requests: int


class FingerprintCards(TypedDict):
    """Aggregate-only TLS / fingerprint summary for the public report."""

    with_ja4: int
    distinct_ja4: int
    ja4_coverage: str
    with_ja3: int
    distinct_ja3: int
    ptr_rate: str  # % of requests with any PTR; never raw hostnames
    mtls_rate: str  # % with tls_client_subject set; never raw subjects
    resume_pct: str
    with_resume_flag: int
    columns_ready: bool


class FingerprintTopRow(TypedDict):
    fingerprint: str
    requests: int
    unique_ips: int


class Ja4ShapeRow(TypedDict):
    shape: str
    requests: int
    distinct_ja4: int


class TlsCurveRow(TypedDict):
    curve: str
    requests: int


class CookieNameTokenRow(TypedDict):
    cookie_name: str
    requests: int
