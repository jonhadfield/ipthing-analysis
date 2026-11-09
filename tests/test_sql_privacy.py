"""Offline privacy contract checks for report SQL.

Public queries may *filter* on identifying columns, but must never project them
as output fields (see SCHEMA.md / AGENTS.md).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"

# Column names that must never appear as SELECT output aliases / bare fields.
FORBIDDEN_OUTPUT = frozenset(
    {
        "user_agent",
        "headers",
        "ptr_hostname",
        "tls_client_subject",
        "body",
        "cookie_names",
        "claimed_xff",
        "cf_connecting_ip",
        "referer",
        "remote_addr",
        "request_uri",
        "ip",
    }
)

_COMMENT_LINE = re.compile(r"--.*?$", re.MULTILINE)
_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)
_AS_ALIAS = re.compile(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    sql = _COMMENT_BLOCK.sub(" ", sql)
    return _COMMENT_LINE.sub(" ", sql)


def _select_lists(sql: str) -> list[str]:
    """Return outermost SELECT projections only (ignore subquery SELECT lists)."""
    text = _strip_comments(sql)
    lists: list[str] = []
    upper = text.upper()
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            i += 1
            continue
        if (
            depth == 0
            and upper.startswith("SELECT", i)
            and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
        ):
            j = i + 6
            # Relative depth inside this SELECT (so nested FROM subqueries are skipped).
            rel = 0
            while j < len(text):
                c = text[j]
                if c == "(":
                    rel += 1
                elif c == ")":
                    rel = max(0, rel - 1)
                elif rel == 0 and upper.startswith("FROM", j) and (
                    j + 4 >= len(text) or not (text[j + 4].isalnum() or text[j + 4] == "_")
                ):
                    lists.append(text[i + 6 : j])
                    i = j
                    break
                j += 1
            else:
                break
            continue
        i += 1
    return lists


def _split_select_items(select_list: str) -> list[str]:
    items: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in select_list:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(buf).strip()
            if item:
                items.append(item)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        items.append(tail)
    return items


def _output_name(item: str) -> str | None:
    """Best-effort output column name for a SELECT item."""
    as_matches = list(_AS_ALIAS.finditer(item))
    if as_matches:
        return as_matches[-1].group(1).lower()
    # Bare identifier / table.column — take the trailing name.
    bare = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", item.strip())
    if bare:
        return bare.group(1).lower()
    return None


def output_columns(sql: str) -> set[str]:
    names: set[str] = set()
    for select_list in _select_lists(sql):
        for item in _split_select_items(select_list):
            # DISTINCT / ALL prefixes
            cleaned = re.sub(r"^(DISTINCT|ALL)\s+", "", item, flags=re.IGNORECASE).strip()
            if cleaned == "*":
                continue
            name = _output_name(cleaned)
            if name:
                names.add(name)
    return names


def test_every_sql_file_avoids_forbidden_output_columns() -> None:
    sql_files = sorted(SQL_DIR.glob("*.sql"))
    assert sql_files, f"no SQL files under {SQL_DIR}"
    violations: list[str] = []
    for path in sql_files:
        projected = output_columns(path.read_text())
        bad = sorted(projected & FORBIDDEN_OUTPUT)
        if bad:
            violations.append(f"{path.name}: {', '.join(bad)}")
    assert not violations, "forbidden identifying columns projected:\n" + "\n".join(
        violations
    )


def test_ua_queries_project_bucket_not_raw_user_agent() -> None:
    for name in ("ua_buckets.sql", "ua_buckets_daily.sql"):
        cols = output_columns((SQL_DIR / name).read_text())
        assert "ua_bucket" in cols
        assert "user_agent" not in cols


def test_fingerprint_presence_queries_do_not_project_identifiers() -> None:
    for name in ("fingerprint_ptr.sql", "fingerprint_mtls.sql"):
        cols = output_columns((SQL_DIR / name).read_text())
        assert not (cols & {"ptr_hostname", "tls_client_subject"})
