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
    layout_height = height if height is not None else (fig.layout.height or 380)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,20,25,0.35)",
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", color="#c5d0db", size=13),
        title=dict(font=dict(size=15, color="#e7ecf1"), x=0.02, xanchor="left"),
        margin=dict(l=48, r=24, t=52, b=44) if not fig.layout.scene else fig.layout.margin,
        height=layout_height,
        legend=dict(
            bgcolor="rgba(26,34,44,0.72)",
            bordercolor="rgba(61,156,240,0.25)",
            borderwidth=1,
            font=dict(size=12),
        ),
        colorway=_PALETTE,
    )
    if fig.layout.scene:
        # Keep 3D margins/camera; only unify fonts/background.
        fig.update_layout(margin=dict(l=10, r=10, t=52, b=10))
        return fig
    fig.update_xaxes(
        gridcolor="rgba(42,53,66,0.65)",
        zerolinecolor="rgba(42,53,66,0.8)",
        linecolor="rgba(90,110,130,0.45)",
        tickfont=dict(color="#9aa7b5"),
        title_font=dict(color="#9aa7b5"),
    )
    fig.update_yaxes(
        gridcolor="rgba(42,53,66,0.65)",
        zerolinecolor="rgba(42,53,66,0.8)",
        linecolor="rgba(90,110,130,0.45)",
        tickfont=dict(color="#9aa7b5"),
        title_font=dict(color="#9aa7b5"),
    )
    return fig


def _fig_html(fig: go.Figure) -> str:
    return pio.to_html(_style(fig), full_html=False, include_plotlyjs=False)


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


def _bars(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    orientation: str = "v",
    color_by: str | None = None,
) -> go.Figure:
    color_col = color_by or (x if orientation == "h" else y)
    fig = px.bar(
        df,
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
    fig.update_layout(coloraxis_showscale=False, bargap=0.28)
    if orientation == "h":
        fig.update_yaxes(autorange="reversed")
    return fig


def _donut(df: pd.DataFrame, *, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.52,
        color_discrete_sequence=_PALETTE,
    )
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        textfont=dict(size=12, color="#c5d0db"),
        marker=dict(line=dict(color="#0f1419", width=2)),
        pull=[0.02] * len(df),
        rotation=40,
    )
    fig.update_layout(showlegend=True)
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
        "daily": _fig_html(_area(daily, x="day", y="requests", title="Requests per day")),
        "access": _fig_html(
            _donut(
                access,
                names="access_mode",
                values="requests",
                title="How clients addressed the service",
            )
        ),
        "access_daily": _fig_html(
            _area(
                access_daily_long,
                x="day",
                y="requests",
                color="mode",
                title="Named vs raw-IP vs other access over time",
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
        "ua": _fig_html(
            _bars_3d(ua, category="ua_bucket", value="requests", title="User-Agent buckets (3D)")
        ),
        "methods": _fig_html(
            _bars(
                methods,
                x="method",
                y="requests",
                title="HTTP methods (GET-only until 23 Sep 2026)",
            )
        ),
        "paths": _fig_html(
            _bars(
                paths.head(12),
                x="requests",
                y="path",
                orientation="h",
                title="Top request paths",
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
