"""Pure renderers: RunMeta -> HTML / Markdown. No MkDocs imports, no I/O."""
from __future__ import annotations

import html

from .run_meta import RunMeta, SourceDetail

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
        date = html.escape(r.date_begin or "—")
        rid = html.escape(r.id)
        rows.append(
            "<tr>"
            f'<td><a class="gf-link" href="runs/{rid}/">{rid}</a></td>'
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
            f'<div class="gf-meta">{html.escape(r.dataset or "—")} · {date}</div>'
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


def _render_source(sd: SourceDetail) -> list[str]:
    out = [f"### {sd.type}", ""]
    if sd.noise_model:
        out.append(f"- **Noise model:** {sd.noise_model}")
    if sd.n_found is not None:
        out.append(f"- **Sources found:** {sd.n_found}")
    if sd.waveform_model:
        wm = (
            f"[{sd.waveform_model}]({sd.waveform_model_link})"
            if sd.waveform_model_link
            else sd.waveform_model
        )
        out.append(f"- **Waveform model:** {wm}")
    if sd.freq_min is not None and sd.freq_max is not None:
        band = f"{sd.freq_min:g}–{sd.freq_max:g} Hz"
        if sd.n_bands:
            band += f" ({sd.n_bands} bands)"
        out.append(f"- **Frequency coverage:** {band}")
    if sd.prior_link:
        out.append(f"- **Prior:** [prior model]({sd.prior_link})")
    if sd.n_posteriors is not None:
        out.append(f"- **Posterior files:** {sd.n_posteriors}")
    out.append("")
    return out


def render_run_page(run: RunMeta) -> str:
    """Return the Markdown body for a single run's detail page."""
    lines: list[str] = [f"# {run.id}", "", _badge(run.status.value), "", run.description, ""]

    analysis: list[str] = []
    if run.domain:
        analysis.append(f"- **Domain:** {run.domain}")
    if run.start_freq_hz is not None:
        analysis.append(f"- **Start frequency:** {run.start_freq_hz:g} Hz")
    if run.end_freq_hz is not None:
        analysis.append(f"- **End frequency:** {run.end_freq_hz:g} Hz")
    if run.sampling_frequency_hz is not None:
        analysis.append(f"- **Sampling frequency:** {run.sampling_frequency_hz:g} Hz")
    if run.observation_time:
        analysis.append(f"- **Observation time:** {run.observation_time}")
    if run.dataset:
        analysis.append(f"- **Dataset:** {run.dataset}")
    if run.date_begin:
        period = run.date_begin + (f" → {run.date_end}" if run.date_end else "")
        analysis.append(f"- **Period:** {period}")
    if run.contact:
        analysis.append(f"- **Contact:** {run.contact}")
    if analysis:
        lines += ["## Analysis", ""] + analysis + [""]

    if run.source_details:
        lines += ["## Sources", ""]
        for sd in run.source_details:
            lines += _render_source(sd)

    lines += ["## Results", ""]
    if run.results.cluster_paths or run.results.cloud_urls:
        for cp in run.results.cluster_paths:
            lines.append(f"- **{cp.host}:** `{cp.path}`")
        for url in run.results.cloud_urls:
            lines.append(f"- [cloud]({url})")
    else:
        lines.append("_No results recorded yet._")

    if run.plots:
        lines += ["", "## Plots", ""]
        for p in run.plots:
            lines.append(f"- {p}")

    return "\n".join(lines) + "\n"
