"""Pure renderers: RunMeta -> HTML / Markdown. No MkDocs imports, no I/O."""
from __future__ import annotations

import html

from .run_meta import RunMeta

_STATUS_CLASS = {
    "complete": "gf-done",
    "running": "gf-run",
    "planned": "gf-plan",
    "archived": "gf-arch",
}


def _badge(status: str) -> str:
    cls = _STATUS_CLASS.get(status, "gf-plan")
    return f'<span class="gf-badge {cls}">{html.escape(status)}</span>'


def _chips(sources: list[str]) -> str:
    return "".join(f'<span class="gf-chip">{html.escape(s)}</span>' for s in sources)


def _result_links(run: RunMeta) -> str:
    parts: list[str] = []
    for cp in run.results.cluster_paths:
        parts.append(
            f'<span class="gf-rpath" title="{html.escape(cp.path)}">'
            f'{html.escape(cp.host)}</span>'
        )
    for url in run.results.cloud_urls:
        parts.append(f'<a class="gf-link" href="{html.escape(url)}">cloud</a>')
    return " · ".join(parts) if parts else "—"


def render_catalog(runs: list[RunMeta]) -> str:
    """Return the toolbar + table view + cards view as a single HTML block."""
    rows: list[str] = []
    cards: list[str] = []
    for r in runs:
        status = r.status.value
        tag = html.escape(r.code.tag or "—")
        date = html.escape(r.date_begin or "—")
        rid = html.escape(r.id)
        rows.append(
            "<tr>"
            f'<td><a class="gf-link" href="runs/{rid}/">{rid}</a>'
            f'<br><span class="gf-sub">{tag}</span></td>'
            f"<td>{_badge(status)}</td>"
            f"<td>{_chips(r.sources)}</td>"
            f'<td>{html.escape(r.dataset or "—")}</td>'
            f"<td>{date}</td>"
            f"<td>{_result_links(r)}</td>"
            "</tr>"
        )
        cards.append(
            '<div class="gf-card">'
            f'<h4><a class="gf-link" href="runs/{rid}/">{rid}</a> {_badge(status)}</h4>'
            f'<div class="gf-meta">{tag} · {date}</div>'
            f"<div>{_chips(r.sources)}</div>"
            f'<div class="gf-desc">{html.escape(r.description)}</div>'
            f'<div class="gf-links">{_result_links(r)}</div>'
            "</div>"
        )

    toolbar = (
        '<div class="gf-toolbar"><span class="gf-label">View:</span>'
        '<div class="gf-toggle">'
        '<button id="gf-btn-table" class="active" '
        "onclick=\"gfSetView('table')\">Table</button>"
        '<button id="gf-btn-cards" onclick="gfSetView(\'cards\')">Cards</button>'
        "</div></div>"
    )
    table = (
        '<div id="view-table" class="gf-view">'
        '<table class="gf-tbl"><thead><tr>'
        "<th>Run</th><th>Status</th><th>Sources</th>"
        "<th>Dataset</th><th>Date</th><th>Results</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )
    cards_html = (
        '<div id="view-cards" class="gf-view gf-hidden">'
        '<div class="gf-cards">' + "".join(cards) + "</div></div>"
    )
    return toolbar + table + cards_html


def render_install_table(runs: list[RunMeta]) -> str:
    """Return a Markdown run -> version table for the installation page."""
    lines = [
        "| Run | TAG_NAME | PHENTAX_VERSION | Status |",
        "|---|---|---|---|",
    ]
    for r in runs:
        tag = r.code.tag or "—"
        ver = r.code.phentax_version or "—"
        # Link the generated .md (not a directory URL) so MkDocs rewrites it to the
        # correct page-relative path and --strict link validation passes.
        lines.append(f"| [{r.id}](runs/{r.id}.md) | `{tag}` | `{ver}` | {r.status.value} |")
    return "\n".join(lines)


def render_run_page(run: RunMeta) -> str:
    """Return the Markdown body for a single run's detail page."""
    lines: list[str] = [f"# {run.id}", "", _badge(run.status.value), "", run.description, ""]

    lines += ["## Details", ""]
    if run.code.tag:
        lines.append(f"- **Code tag:** `{run.code.tag}`")
    if run.code.phentax_version:
        lines.append(f"- **phentax:** `{run.code.phentax_version}`")
    if run.code.code_link:
        lines.append(f"- **Code:** {run.code.code_link}")
    if run.sources:
        lines.append(f"- **Sources:** {', '.join(run.sources)}")
    if run.dataset:
        lines.append(f"- **Dataset:** {run.dataset}")
    if run.observation_time:
        lines.append(f"- **Observation time:** {run.observation_time}")
    if run.date_begin:
        lines.append(f"- **Period:** {run.date_begin} → {run.date_end or ''}")
    if run.config:
        lines.append(f"- **Config:** {run.config}")
    if run.contact:
        lines.append(f"- **Contact:** {run.contact}")

    lines += ["", "## Results", ""]
    if run.results.cluster_paths or run.results.cloud_urls:
        for cp in run.results.cluster_paths:
            lines.append(f"- **{cp.host}:** `{cp.path}`")
        for url in run.results.cloud_urls:
            lines.append(f"- [cloud]({url})")
    else:
        lines.append("_No results recorded yet._")

    if run.plots:  # reserved for future figures
        lines += ["", "## Plots", ""]
        for p in run.plots:
            lines.append(f"- {p}")

    return "\n".join(lines) + "\n"
