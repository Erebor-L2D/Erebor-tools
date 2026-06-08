"""MkDocs hooks: generate per-run pages and inject the catalog.

All rendering lives in erebortools.website.render; this module only wires it into
the build. Run metadata is read from the repo-root runs/ directory.
"""
from __future__ import annotations

from pathlib import Path

from mkdocs.structure.files import File

from erebortools.website.render import (
    render_catalog,
    render_run_page,
)
from erebortools.website.run_meta import load_runs

_RUNS_DIR = Path("runs")


def _runs():
    return load_runs(_RUNS_DIR)


def on_files(files, config):
    """Add one generated Markdown page per run under docs runs/<id>.md."""
    for run in _runs():
        files.append(
            File.generated(
                config,
                f"runs/{run.id}.md",
                content=render_run_page(run),
            )
        )
    return files


def on_page_markdown(markdown, page, config, files):
    """Replace {{ catalog }} on Home."""
    src = page.file.src_uri
    if src == "index.md" and "{{ catalog }}" in markdown:
        markdown = markdown.replace("{{ catalog }}", render_catalog(_runs()))
    return markdown
