"""Build the static analysis report from Neon (read-only)."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import psycopg
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
TEMPLATE_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
SITE_DIR = ROOT / "docs"
IPV6_ENABLED = pd.Timestamp("2026-09-25")

# Cool steel → cyan palette (avoids flat single hues and purple defaults).
_PALETTE = ["#2a6f97", "#3d9cf0", "#56cfe1", "#72efdd", "#80ed99", "#f4d35e", "#ee6c4d", "#9aa7b5"]
_AREA_SCALE = [[0.0, "#0b1c2c"], [0.45, "#1b4d6e"], [1.0, "#56cfe1"]]
_BAR_SCALE = [[0.0, "#1a3a4a"], [0.35, "#2a6f97"], [0.7, "#3d9cf0"], [1.0, "#72efdd"]]


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


def _style(fig: go.Figure, *, height: int | None = None) -> go.Figure:
    layout_height = height if height is not None else (fig.layout.height or 360)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,20,25,0.35)",
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", color="#c5d0db", size=12),
        title=dict(font=dict(size=14, color="#e7ecf1"), x=0.02, xanchor="left"),
        margin=dict(l=40, r=16, t=48, b=88) if not fig.layout.scene else fig.layout.margin,
        height=layout_height,
        autosize=True,
        legend=dict(
            bgcolor="rgba(26,34,44,0.85)",
            bordercolor="rgba(61,156,240,0.25)",
            borderwidth=1,
            font=dict(size=11),
            orientation="h",
            yanchor="top",
            y=-0.18,
            x=0,
            xanchor="left",
        ),
        colorway=_PALETTE,
    )
    if fig.layout.scene:
        # Keep 3D margins/camera; only unify fonts/background.
        fig.update_layout(margin=dict(l=10, r=10, t=48, b=10))
        return fig
    fig.update_xaxes(
        gridcolor="rgba(42,53,66,0.65)",
        zerolinecolor="rgba(42,53,66,0.8)",
        linecolor="rgba(90,110,130,0.45)",
        tickfont=dict(color="#9aa7b5", size=11),
        title_font=dict(color="#9aa7b5", size=11),
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="rgba(42,53,66,0.65)",
        zerolinecolor="rgba(42,53,66,0.8)",
        linecolor="rgba(90,110,130,0.45)",
        tickfont=dict(color="#9aa7b5", size=11),
        title_font=dict(color="#9aa7b5", size=11),
        automargin=True,
    )
    return fig


def _fig_html(fig: go.Figure) -> str:
    return pio.to_html(
        _style(fig),
        full_html=False,
        include_plotlyjs=False,
        config={
            "responsive": True,
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


def _area(df: pd.DataFrame, *, x: str, y: str, title: str, color: str | None = None) -> go.Figure:
    series_scales = [
        [[0.0, "#0b1c2c"], [1.0, c]] for c in _PALETTE
    ]
    if color:
        fig = px.area(df, x=x, y=y, color=color, title=title, color_discrete_sequence=_PALETTE)
        for i, trace in enumerate(fig.data):
            scale = series_scales[i % len(series_scales)]
            trace.update(
                line=dict(width=1.6, color=_PALETTE[i % len(_PALETTE)]),
                opacity=0.95,
                fillgradient=dict(type="vertical", colorscale=scale),
            )
    else:
        fig = px.area(df, x=x, y=y, title=title)
        fig.update_traces(
            line=dict(color="#56cfe1", width=2.2),
            fillgradient=dict(type="vertical", colorscale=_AREA_SCALE),
        )
    return fig


def _donut(df: pd.DataFrame, *, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.55,
        color_discrete_sequence=_PALETTE,
    )
    # Labels in the legend; percent inside the ring — avoids clipped outside labels on phones.
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(size=11, color="#e7ecf1"),
        insidetextorientation="horizontal",
        marker=dict(line=dict(color="#0f1419", width=2)),
        pull=[0.015] * len(df),
        rotation=40,
    )
    fig.update_layout(showlegend=True, height=390, margin=dict(l=16, r=16, t=48, b=72))
    return fig


def _short_label(value: object, limit: int = 28) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _empty_chart(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=280,
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="#9aa7b5"),
            )
        ],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _bars(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    color_by: str | None = None,
) -> go.Figure:
    if df.empty:
        return _empty_chart(title, "No data yet")
    plot_df = df.copy()
    # Shorten categorical axis labels so horizontal charts fit narrow screens.
    label_col = y if orientation == "h" else x
    if label_col in plot_df.columns and plot_df[label_col].dtype == object:
        plot_df[label_col] = plot_df[label_col].map(_short_label)

    color_col = color_by or (x if orientation == "h" else y)
    fig = px.bar(
        plot_df,
        x=x,
        y=y,
        title=title,
        orientation=orientation,
        color=color_col,
        color_continuous_scale=_BAR_SCALE,
    )
    fig.update_traces(
        marker=dict(
            cornerradius=10,
            line=dict(width=1, color="rgba(226,240,255,0.35)"),
        ),
        hovertemplate="%{y}: %{x}<extra></extra>"
        if orientation == "h"
        else "%{x}: %{y}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=False, bargap=0.28, showlegend=False)
    if orientation == "h":
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(300, 28 * len(plot_df) + 80), margin=dict(l=8, r=16, t=48, b=40))
    return fig


def _bars_3d(df: pd.DataFrame, *, category: str, value: str, title: str) -> go.Figure:
    """Compact categorical 3D bars — depth cue without a full dashboard look."""
    cats = df[category].astype(str).tolist()
    vals = [float(v) for v in df[value].tolist()]
    xmax = max(vals) if vals else 1.0
    meshes: list[go.Mesh3d] = []
    # Rectangular prism faces (two triangles each): bottom, top, and four sides.
    faces_i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    faces_j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    faces_k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    for i, (cat, val) in enumerate(zip(cats, vals, strict=True)):
        x0, x1 = i - 0.32, i + 0.32
        y0, y1 = 0.0, val
        z0, z1 = 0.0, 0.55
        t = val / xmax if xmax else 0.0
        color = f"rgb({int(42 + t * 70)},{int(111 + t * 90)},{int(151 + t * 80)})"
        meshes.append(
            go.Mesh3d(
                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                z=[z0, z0, z0, z0, z1, z1, z1, z1],
                i=faces_i,
                j=faces_j,
                k=faces_k,
                color=color,
                opacity=0.94,
                flatshading=True,
                hovertemplate=f"{cat}<br>{value}={val:,.0f}<extra></extra>",
                name=cat,
                showscale=False,
            )
        )
    fig = go.Figure(data=meshes)
    fig.update_layout(
        title=title,
        height=440,
        showlegend=False,
        margin=dict(l=10, r=10, t=52, b=10),
        scene=dict(
            xaxis=dict(
                tickmode="array",
                tickvals=list(range(len(cats))),
                ticktext=cats,
                title="",
                backgroundcolor="rgba(15,20,25,0.2)",
                gridcolor="rgba(42,53,66,0.7)",
                showspikes=False,
            ),
            yaxis=dict(
                title=value,
                backgroundcolor="rgba(15,20,25,0.2)",
                gridcolor="rgba(42,53,66,0.7)",
                showspikes=False,
            ),
            zaxis=dict(
                title="",
                range=[-0.1, 1.2],
                showticklabels=False,
                backgroundcolor="rgba(15,20,25,0.2)",
                gridcolor="rgba(42,53,66,0.5)",
                showspikes=False,
            ),
            camera=dict(eye=dict(x=1.6, y=1.4, z=1.0)),
            aspectmode="manual",
            aspectratio=dict(x=1.5, y=1.0, z=0.4),
        ),
    )
    return fig


_CIPHER_NAMES: dict[int, str] = {
    4865: "TLS_AES_128_GCM_SHA256",
    4866: "TLS_AES_256_GCM_SHA384",
    4867: "TLS_CHACHA20_POLY1305_SHA256",
    49195: "ECDHE_ECDSA_AES_128_GCM_SHA256",
    49199: "ECDHE_RSA_AES_128_GCM_SHA256",
    49200: "ECDHE_RSA_AES_256_GCM_SHA384",
    52392: "ECDHE_RSA_CHACHA20_POLY1305",
    52393: "ECDHE_ECDSA_CHACHA20_POLY1305",
    49196: "ECDHE_ECDSA_AES_256_GCM_SHA384",
}

_DOW_LABELS = {
    1: "Mon",
    2: "Tue",
    3: "Wed",
    4: "Thu",
    5: "Fri",
    6: "Sat",
    7: "Sun",
}


def _cipher_label(cipher_id: object) -> str:
    try:
        cid = int(cipher_id)
    except (TypeError, ValueError):
        return str(cipher_id)
    name = _CIPHER_NAMES.get(cid)
    return f"{name} ({cid})" if name else f"suite {cid}"


def _heatmap(df: pd.DataFrame, *, title: str) -> go.Figure:
    if df.empty:
        return _empty_chart(title, "No data yet")
    grid = (
        df.pivot_table(index="dow", columns="hour", values="requests", aggfunc="sum")
        .reindex(index=range(1, 8), columns=range(24), fill_value=0)
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=grid.values,
            x=[str(h) for h in grid.columns],
            y=[_DOW_LABELS.get(i, str(i)) for i in grid.index],
            colorscale=_BAR_SCALE,
            hovertemplate=" %{y} %{x}:00 UTC<br>requests=%{z}<extra></extra>",
            colorbar=dict(title="requests"),
        )
    )
    fig.update_layout(
        title=title,
        height=360,
        xaxis_title="Hour (UTC)",
        yaxis_title="Day",
        margin=dict(l=48, r=24, t=48, b=48),
    )
    return fig


def build() -> Path:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    if STATIC_DIR.is_dir():
        for path in STATIC_DIR.iterdir():
            if path.is_file():
                shutil.copy2(path, SITE_DIR / path.name)

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
        status_codes = _read_sql(conn, "status_codes.sql")
        tls_ciphers = _read_sql(conn, "tls_ciphers.sql")
        tls_alpn = _read_sql(conn, "tls_alpn.sql")
        response_formats = _read_sql(conn, "response_formats.sql")
        referer_overview = _read_sql(conn, "referer_overview.sql").iloc[0].to_dict()
        referer_hosts = _read_sql(conn, "referer_hosts.sql")
        hour_of_week = _read_sql(conn, "hour_of_week.sql")
        path_themes = _read_sql(conn, "path_themes.sql")
        probe_paths_daily = _read_sql(conn, "probe_paths_daily.sql")
        latency = _read_sql(conn, "latency.sql").iloc[0].to_dict()
        ip_family = _read_sql(conn, "ip_family.sql")
        ip_family_daily = _read_sql(conn, "ip_family_daily.sql")
        ipv6_orgs = _read_sql(conn, "ipv6_orgs.sql")

    if not tls_ciphers.empty:
        tls_ciphers = tls_ciphers.copy()
        tls_ciphers["cipher"] = tls_ciphers["cipher_id"].map(_cipher_label)

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

    probe_daily_long = probe_paths_daily.melt(
        id_vars=["day"],
        value_vars=["root_ok", "probe_or_404"],
        var_name="kind",
        value_name="count",
    )
    probe_daily_long["kind"] = probe_daily_long["kind"].map(
        {
            "root_ok": "root OK (/)",
            "probe_or_404": "non-root / 404",
        }
    )

    family_daily = ip_family_daily.copy()
    family_total = family_daily["ipv4_requests"] + family_daily["ipv6_requests"]
    family_daily["ipv6_share_pct"] = (
        family_daily["ipv6_requests"] / family_total.where(family_total > 0) * 100
    ).fillna(0.0).round(2)

    # IPv6 was enabled on 2026-09-25; share is only meaningful from then on.
    since_v6 = family_daily[pd.to_datetime(family_daily["day"]) >= IPV6_ENABLED]
    v4_since = int(since_v6["ipv4_requests"].sum())
    v6_since = int(since_v6["ipv6_requests"].sum())
    v6_row = next(
        (row for row in ip_family.to_dict(orient="records") if row["family"] == "IPv6"), {}
    )
    ipv6_cards = {
        "requests": int(v6_row.get("requests") or 0),
        "unique_ips": int(v6_row.get("unique_ips") or 0),
        "share_pct": f"{v6_since / (v4_since + v6_since) * 100:.1f}%"
        if (v4_since + v6_since)
        else "—",
        "first_day": v6_row.get("first_day") or "—",
    }
    # Start the share chart a week early so the switch-on is visible.
    family_daily_recent = family_daily[
        pd.to_datetime(family_daily["day"]) >= IPV6_ENABLED - pd.Timedelta(days=7)
    ]

    referer_top = referer_hosts[
        ~referer_hosts["referer_host"].isin(["(none)"])
    ].head(12)

    charts = {
        "daily": _fig_html(_area(daily, x="day", y="requests", title="Requests per day")),
        "access": _fig_html(
            _donut(
                access,
                names="access_mode",
                values="requests",
                title="How clients addressed the service (since 23 Sep 2026)",
            )
        ),
        "access_daily": _fig_html(
            _area(
                access_daily_long,
                x="day",
                y="requests",
                color="mode",
                title="Named vs raw-IP vs other access over time (Host gap 19 Dec 2025–23 Sep 2026)",
            )
        ),
        "countries": _fig_html(
            _bars(
                countries.head(12),
                x="ips",
                y="country",
                orientation="h",
                title="Top countries by distinct IPs",
            )
        ),
        "orgs": _fig_html(
            _bars(
                orgs.head(12),
                x="ips",
                y="org",
                orientation="h",
                title="Top networks (org / ASN label) by distinct IPs",
            )
        ),
        "tls": _fig_html(_donut(tls, names="tls", values="requests", title="TLS versions")),
        "proto": _fig_html(
            _donut(proto, names="proto", values="requests", title="HTTP protocol")
        ),
        "tls_ciphers": _fig_html(
            _bars(
                tls_ciphers.head(12),
                x="requests",
                y="cipher",
                orientation="h",
                title="Top TLS cipher suites",
            )
            if not tls_ciphers.empty
            else _empty_chart("Top TLS cipher suites", "No cipher data yet")
        ),
        "tls_alpn": _fig_html(
            _donut(tls_alpn, names="alpn", values="requests", title="TLS ALPN")
        ),
        "ua": _fig_html(
            _bars_3d(ua, category="ua_bucket", value="requests", title="User-Agent buckets (3D)")
        ),
        "ua_mobile": _fig_html(
            _bars(ua, x="ua_bucket", y="requests", title="User-Agent buckets")
        ),
        "methods": _fig_html(
            _bars(
                methods,
                x="method",
                y="requests",
                title="HTTP methods since 23 Sep 2026 (when non-GET was allowed)",
            )
        ),
        "paths": _fig_html(
            _bars(
                paths.head(12),
                x="requests",
                y="path",
                orientation="h",
                title="Top non-root paths (404 / probes)",
            )
        ),
        "path_themes": _fig_html(
            _bars(
                path_themes,
                x="requests",
                y="path_theme",
                orientation="h",
                title="Non-root path themes",
            )
        ),
        "probe_paths_daily": _fig_html(
            _area(
                probe_daily_long,
                x="day",
                y="count",
                color="kind",
                title="Root OK vs non-root / 404 over time",
            )
        ),
        "query_keys": _fig_html(
            _bars(
                query_keys.head(15),
                x="requests",
                y="param_key",
                orientation="h",
                title="Top query parameter names (not values)",
            )
        ),
        "host_sni": _fig_html(
            _donut(
                host_sni,
                names="host_sni_relation",
                values="requests",
                title="HTTP Host vs TLS SNI (since 23 Sep 2026)",
            )
        ),
        "status": _fig_html(
            _donut(status_codes, names="status", values="requests", title="HTTP status codes")
        ),
        "formats": _fig_html(
            _donut(
                response_formats,
                names="response_format",
                values="requests",
                title="Response format",
            )
        ),
        "referers": _fig_html(
            _bars(
                referer_top,
                x="requests",
                y="referer_host",
                orientation="h",
                title="Top referer hosts (excluding none)",
            )
        ),
        "ip_family": _fig_html(
            _donut(
                ip_family[ip_family["family"] != "loopback"],
                names="family",
                values="requests",
                title="Requests by address family",
            )
        ),
        "ipv6_share": _fig_html(
            _area(
                family_daily_recent,
                x="day",
                y="ipv6_share_pct",
                title="IPv6 share of daily requests (%), from a week before enablement",
            )
        ),
        "heatmap": _fig_html(
            _heatmap(hour_of_week, title="Requests by day-of-week and hour (UTC)")
        ),
    }

    def _ms(value: object) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "—"
        return f"{float(value):,.0f}"

    latency_cards = {
        "with_duration": int(latency.get("with_duration") or 0),
        "p50_ms": _ms(latency.get("p50_ms")),
        "p95_ms": _ms(latency.get("p95_ms")),
        "p99_ms": _ms(latency.get("p99_ms")),
    }

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("report.html.j2").render(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        overview=overview,
        probe=probe,
        latency=latency_cards,
        ipv6=ipv6_cards,
        ip_family=ip_family.to_dict(orient="records"),
        ipv6_orgs=ipv6_orgs.to_dict(orient="records"),
        referer_overview=referer_overview,
        countries=countries.to_dict(orient="records"),
        orgs=orgs.to_dict(orient="records"),
        access=access.to_dict(orient="records"),
        top_hosts=top_hosts.to_dict(orient="records"),
        methods=methods.to_dict(orient="records"),
        paths=paths.to_dict(orient="records"),
        path_themes=path_themes.to_dict(orient="records"),
        query_keys=query_keys.to_dict(orient="records"),
        host_sni=host_sni.to_dict(orient="records"),
        status_codes=status_codes.to_dict(orient="records"),
        response_formats=response_formats.to_dict(orient="records"),
        tls_ciphers=tls_ciphers.to_dict(orient="records") if not tls_ciphers.empty else [],
        referer_hosts=referer_hosts.to_dict(orient="records"),
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
