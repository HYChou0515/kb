"""Read-only preview renderers shared between the chat bubbles and
the editor's Preview view toggle.

Each `render_*` returns an HTML string suitable for `ui.html(...,
sanitize=False)`.  Agent / case files are trusted; the inputs are
already escaped where needed (mistune handles markdown; json/csv
escape via `html.escape` and pandas' `to_html(escape=True)`).
"""

from __future__ import annotations

import html as html_lib
import io
import json
from pathlib import Path

import mistune

PREVIEW_SUFFIXES = frozenset(
    {".md", ".markdown", ".json", ".jsonl", ".csv"}
)


def is_previewable(path: Path) -> bool:
    return path.suffix.lower() in PREVIEW_SUFFIXES


# mistune is CJK-tolerant — handles `**A) 你有特定 lot:**把` correctly
# where CommonMark's right-flanking rule trips on punctuation-then-letter.
_md_render = mistune.create_markdown(plugins=["table", "strikethrough", "url"])


def render_md(text: str) -> str:
    return _md_render(text or "")


def render_json(text: str) -> str:
    """Pretty-print a JSON document as a <pre> block.  Parse failure
    returns a short error notice instead of raising."""
    if not (text or "").strip():
        return '<div class="rca-preview-empty">(empty file)</div>'
    try:
        parsed = json.loads(text)
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError) as exc:
        return (
            '<div class="rca-preview-empty">parse failed: '
            f"{html_lib.escape(str(exc))}</div>"
        )
    return f"<pre>{html_lib.escape(pretty)}</pre>"


def render_jsonl(text: str) -> str:
    """One pretty-printed block per non-empty JSONL line, prefixed
    with its 1-based line number.  Malformed lines are flagged
    inline rather than aborting the whole render."""
    parts: list[str] = []
    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            pretty = json.dumps(json.loads(line), indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError) as exc:
            pretty = f"(line {idx} parse failed: {exc})"
        parts.append(
            f'<div style="margin-bottom:0.7em;">'
            f'<div style="font:10.5px ui-monospace,monospace;color:#999;'
            f'margin-bottom:2px;">#{idx}</div>'
            f"<pre>{html_lib.escape(pretty)}</pre></div>"
        )
    if not parts:
        return '<div class="rca-preview-empty">(empty file)</div>'
    return "\n".join(parts)


def render_csv(text: str) -> str:
    """Render CSV as an HTML table via pandas.  Truncates to 1000
    rows so a giant CSV doesn't freeze the UI."""
    if not (text or "").strip():
        return '<div class="rca-preview-empty">(empty file)</div>'
    try:
        import pandas as pd

        df = pd.read_csv(io.StringIO(text))
    except Exception as exc:  # noqa: BLE001 — pandas raises many types
        return (
            '<div class="rca-preview-empty">parse failed: '
            f"{html_lib.escape(str(exc))}</div>"
        )
    total = len(df)
    truncated = ""
    if total > 1000:
        df = df.head(1000)
        truncated = (
            f'<div class="rca-preview-empty">'
            f"showing first 1000 of {total} rows</div>"
        )
    table = df.to_html(
        index=False, classes="rca-csv-table", border=0, escape=True
    )
    return truncated + table


def render_for_path(path: Path, text: str) -> str:
    """Dispatch by file suffix.  Returns "(no preview)" placeholder
    for unsupported types so the caller doesn't have to branch."""
    suf = path.suffix.lower()
    if suf in (".md", ".markdown"):
        return render_md(text)
    if suf == ".json":
        return render_json(text)
    if suf == ".jsonl":
        return render_jsonl(text)
    if suf == ".csv":
        return render_csv(text)
    return '<div class="rca-preview-empty">(no preview for this file type)</div>'
