"""Build the static analysis report from Neon (read-only)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
import psycopg
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
TEMPLATE_DIR = ROOT / "templates"
SITE_DIR = ROOT / "docs"


def _connect() -> psycopg.Connection:
    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy .env.example to .env and use a read-only Neon URL."
        )
    # Prefer direct endpoint for analytics queries when a pooler URL is supplied.
    url = url.replace("-pooler.", ".")
    return psycopg.connect(url)


def _read_sql(conn: psycopg.Connection, name: str) -> pd.DataFrame:
    sql = (SQL_DIR / name).read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def _fig_html(fig) -> str:
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
        font=dict(family="IBM Plex Sans, system-ui, sans-serif"),
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def build() -> Path:
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        overview = _read_sql(conn, "overview.sql").iloc[0].to_dict()
        daily = _read_sql(conn, "daily_volume.sql")
        countries = _read_sql(conn, "top_countries.sql")
        orgs = _read_sql(conn, "top_orgs.sql")
        tls = _read_sql(conn, "tls_versions.sql")
        proto = _read_sql(conn, "http_proto.sql")
        ua = _read_sql(conn, "ua_buckets.sql")
        access = _read_sql(conn, "access_mode.sql")
        access_daily = _read_sql(conn, "access_mode_daily.sql")
        top_hosts = _read_sql(conn, "top_hosts.sql")
        probe = _read_sql(conn, "probe_overview.sql").iloc[0].to_dict()
        methods = _read_sql(conn, "methods.sql")
        paths = _read_sql(conn, "paths.sql")
        query_keys = _read_sql(conn, "query_param_keys.sql")
        host_sni = _read_sql(conn, "host_sni.sql")

    access_daily_long = access_daily.melt(
        id_vars=["day"],
        value_vars=["named_requests", "raw_ip_requests", "other_host_requests", "unset_requests"],
        var_name="mode",
        value_name="requests",
    )
    access_daily_long["mode"] = access_daily_long["mode"].map(
        {
            "named_requests": "named (ipthing.net)",
            "raw_ip_requests": "raw IP",
            "other_host_requests": "other Host",
            "unset_requests": "Host unset",
        }
    )

    charts = {
        "daily": _fig_html(
            px.area(daily, x="day", y="requests", title="Requests per day")
        ),
        "access": _fig_html(
            px.pie(
                access,
                names="access_mode",
                values="requests",
                title="How clients addressed the service",
            )
        ),
        "access_daily": _fig_html(
            px.area(
                access_daily_long,
                x="day",
                y="requests",
                color="mode",
                title="Named vs raw-IP vs other access over time",
            )
        ),
        "countries": _fig_html(
            px.bar(
                countries.head(12),
                x="ips",
                y="country",
                orientation="h",
                title="Top countries by distinct IPs",
            ).update_yaxes(autorange="reversed")
        ),
        "orgs": _fig_html(
            px.bar(
                orgs.head(12),
                x="ips",
                y="org",
                orientation="h",
                title="Top networks (org / ASN label) by distinct IPs",
            ).update_yaxes(autorange="reversed")
        ),
        "tls": _fig_html(px.pie(tls, names="tls", values="requests", title="TLS versions")),
        "proto": _fig_html(
            px.pie(proto, names="proto", values="requests", title="HTTP protocol")
        ),
        "ua": _fig_html(
            px.bar(ua, x="ua_bucket", y="requests", title="User-Agent buckets (heuristic)")
        ),
        "methods": _fig_html(
            px.bar(methods, x="method", y="requests", title="HTTP methods")
        ),
        "paths": _fig_html(
            px.bar(
                paths.head(12),
                x="requests",
                y="path",
                orientation="h",
                title="Top request paths",
            ).update_yaxes(autorange="reversed")
        ),
        "query_keys": _fig_html(
            px.bar(
                query_keys.head(15),
                x="requests",
                y="param_key",
                orientation="h",
                title="Top query parameter names (not values)",
            ).update_yaxes(autorange="reversed")
        ),
        "host_sni": _fig_html(
            px.pie(
                host_sni,
                names="host_sni_relation",
                values="requests",
                title="HTTP Host vs TLS SNI",
            )
        ),
    }

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("report.html.j2").render(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        overview=overview,
        probe=probe,
        countries=countries.to_dict(orient="records"),
        orgs=orgs.to_dict(orient="records"),
        access=access.to_dict(orient="records"),
        top_hosts=top_hosts.to_dict(orient="records"),
        methods=methods.to_dict(orient="records"),
        paths=paths.to_dict(orient="records"),
        query_keys=query_keys.to_dict(orient="records"),
        host_sni=host_sni.to_dict(orient="records"),
        charts=charts,
    )
    out = SITE_DIR / "index.html"
    out.write_text(html)
    return out


def main() -> None:
    path = build()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
