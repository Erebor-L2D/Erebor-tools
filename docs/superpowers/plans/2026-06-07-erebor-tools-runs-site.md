# Erebor-tools Runs Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a MkDocs Material site in the `Erebor-tools` repo that catalogs Erebor global-fit runs from one `meta.yaml` per run, with a table/cards catalog, per-run detail pages, an auto-generated installation table, and a converter that drafts a run's `meta.yaml` from its emitted `global_metadata.json`.

**Architecture:** `meta.yaml` files under `runs/<id>/` are the single source of truth, validated by a pydantic `RunMeta` model. A pure `erebor_site.render` module turns `RunMeta` objects into HTML/Markdown. A thin `hooks.py` MkDocs hook wires those renderers into the build (generating run pages, injecting the catalog, regenerating the install table). `erebor_site.from_metadata` is a standalone CLI that maps `global_metadata.json` → a draft `meta.yaml`. Deployed to public GitHub Pages via GitHub Actions.

**Tech Stack:** Python 3.12, uv, MkDocs + mkdocs-material, pydantic v2, PyYAML, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-06-07-erebor-tools-runs-site-design.md` (this repo, alongside this plan).

> **Update (2026-06-08): module relocated.** The Python package was renamed
> `erebor_site` → `erebortools` and moved to a **src layout**: the website code now
> lives in `src/erebortools/website/` (`run_meta.py`, `render.py`, `from_metadata.py`).
> Wherever this plan says `erebor_site/<x>.py` read `src/erebortools/website/<x>.py`,
> and wherever it says `from erebor_site.<x>` / `python -m erebor_site.<x>` read
> `erebortools.website.<x>`. `pyproject.toml` uses `name = "erebortools"` and
> `[tool.hatch.build.targets.wheel] packages = ["src/erebortools"]`. `tests/`, `runs/`,
> `docs/`, `hooks.py`, and `mkdocs.yml` stay at the repo root.

---

## Working directory & conventions

- **All paths below are relative to the Erebor-tools repo root:** `/Users/alessandrosantini/reps/globalift/erebor/results_misc/Erebor-tools`. `cd` there before starting.
- That repo is its **own git repository** (remote `Erebor-L2D/Erebor-tools`). All `git commit` steps in this plan commit **there**, not in the parent `erebor` repo.
- Run all Python via `uv run …` (matches the rest of the codebase). The docs site is pure-Python (no CUDA/compiler needed).
- The **full-stack per-run `pyproject.toml` install** is intentionally **out of scope** here (tracked as a separate DRAFT spec). Do not implement `gen_install.py`, per-run `pyproject.toml`, or `install.sh` in this plan.

## File structure (what gets created)

```
Erebor-tools/
├── pyproject.toml              # NEW: uv/hatchling project; docs + dev deps
├── mkdocs.yml                  # NEW: MkDocs Material config + hooks wiring
├── hooks.py                    # NEW: MkDocs hook (thin adapter over erebor_site)
├── erebor_site/
│   ├── __init__.py             # NEW: package marker
│   ├── run_meta.py             # NEW: pydantic RunMeta + load_runs()
│   ├── render.py               # NEW: pure RunMeta -> HTML/Markdown renderers
│   └── from_metadata.py        # NEW: global_metadata.json -> meta.yaml CLI
├── runs/
│   ├── _template/meta.yaml     # NEW: copy-to-add template (skipped by loader)
│   └── run-0/meta.yaml         # NEW: real run (cdl1-run0)
├── docs/
│   ├── index.md                # NEW: intro + {{ catalog }}
│   ├── installation.md         # NEW: existing content; run table -> {{ install_table }}
│   ├── adding-a-run.md         # NEW: contributor guide
│   └── assets/
│       ├── catalog.css         # NEW: badges/chips/table/cards/toggle styling
│       └── catalog.js          # NEW: view toggle + localStorage
├── tests/
│   ├── test_run_meta.py        # NEW
│   ├── test_render.py          # NEW
│   ├── test_from_metadata.py   # NEW
│   └── data/global_metadata.sample.json  # NEW: converter fixture
└── .github/workflows/docs.yml  # NEW: build + deploy to GitHub Pages
```

**Boundaries:** `run_meta.py` owns the schema + loading; `render.py` is pure (no MkDocs, no I/O) so it is trivially unit-testable; `hooks.py` is the only MkDocs-aware module and contains no rendering logic; `from_metadata.py` is independent of MkDocs and of `render.py`.

---

## Task 1: Project scaffold & tooling

**Files:**
- Create: `pyproject.toml`
- Create: `erebor_site/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "erebor-tools-site"
version = "0.0.0"
description = "Erebor global-fit runs catalog website"
requires-python = ">=3.12"
dependencies = [
  "mkdocs-material>=9.5",
  "pydantic>=2.6",
  "pyyaml>=6.0",
  "pymdown-extensions>=10.7",
]

[dependency-groups]
dev = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["erebor_site"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create the package + test markers**

`erebor_site/__init__.py`:
```python
"""Erebor-tools runs catalog site helpers."""
```

`tests/__init__.py`:
```python
```
(empty file)

- [ ] **Step 3: Sync the environment and verify tooling**

Run: `uv run mkdocs --version`
Expected: prints a version like `mkdocs, version 1.6.x` (uv creates the venv and installs deps on first run).

Run: `uv run pytest -q`
Expected: `no tests ran` (exit code 5) — acceptable; confirms pytest is installed.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml erebor_site/__init__.py tests/__init__.py
git commit -m "chore: scaffold mkdocs docs-site project (uv + pydantic)"
```

---

## Task 2: `RunMeta` schema + loader

**Files:**
- Create: `erebor_site/run_meta.py`
- Test: `tests/test_run_meta.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_run_meta.py`:
```python
import textwrap
import pytest
from pathlib import Path
from pydantic import ValidationError
from erebor_site.run_meta import RunMeta, load_run, load_runs


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))
    return path


def test_minimal_valid_applies_defaults():
    m = RunMeta.model_validate(
        {"id": "run-0", "status": "complete", "description": "test run"}
    )
    assert m.id == "run-0"
    assert m.status.value == "complete"
    assert m.sources == []
    assert m.results.cluster_paths == []
    assert m.code.tag is None


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate(
            {"id": "x", "status": "finished", "description": "d"}
        )


def test_missing_required_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate({"id": "x", "status": "complete"})


def test_unknown_key_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate(
            {"id": "x", "status": "complete", "description": "d", "tagg": "oops"}
        )


def test_load_runs_skips_template_and_sorts(tmp_path):
    runs = tmp_path / "runs"
    _write(runs / "_template" / "meta.yaml",
           "id: tmpl\nstatus: planned\ndescription: template\n")
    _write(runs / "run-1" / "meta.yaml",
           "id: run-1\nstatus: running\ndescription: one\n")
    _write(runs / "run-0" / "meta.yaml",
           "id: run-0\nstatus: complete\ndescription: zero\n")
    loaded = load_runs(runs)
    assert [r.id for r in loaded] == ["run-0", "run-1"]


def test_load_run_error_names_file(tmp_path):
    bad = _write(tmp_path / "runs" / "bad" / "meta.yaml",
                 "id: bad\nstatus: nope\ndescription: d\n")
    with pytest.raises(ValueError) as exc:
        load_run(bad)
    assert "bad/meta.yaml" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_run_meta.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'erebor_site.run_meta'`.

- [ ] **Step 3: Implement `erebor_site/run_meta.py`**

```python
"""Run metadata schema (the single source of truth for each global-fit run)."""
from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    planned = "planned"
    running = "running"
    complete = "complete"
    archived = "archived"


class CodeInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tag: str | None = None
    phentax_version: str | None = None
    code_link: str | None = None


class ClusterPath(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str
    path: str


class Results(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cluster_paths: list[ClusterPath] = Field(default_factory=list)
    cloud_urls: list[str] = Field(default_factory=list)


class RunMeta(BaseModel):
    """Validated metadata for one global-fit run."""

    model_config = ConfigDict(extra="forbid")

    id: str
    status: Status
    description: str
    date_begin: str | None = None
    date_end: str | None = None
    code: CodeInfo = Field(default_factory=CodeInfo)
    sources: list[str] = Field(default_factory=list)
    dataset: str | None = None
    observation_time: str | None = None
    results: Results = Field(default_factory=Results)
    config: str | None = None
    contact: str | None = None
    plots: list = Field(default_factory=list)  # reserved for future per-run figures


def load_run(path: Path) -> RunMeta:
    """Load and validate a single meta.yaml, raising ValueError naming the file."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text()) or {}
        return RunMeta.model_validate(data)
    except Exception as exc:  # noqa: BLE001 - re-raise with file context
        # Show the last two path parts (e.g. "run-0/meta.yaml") for a friendly message.
        label = "/".join(path.parts[-2:])
        raise ValueError(f"Invalid run metadata in {label}: {exc}") from exc


def load_runs(runs_dir: Path) -> list[RunMeta]:
    """Load every runs/*/meta.yaml (skipping _underscore dirs), sorted by id."""
    runs_dir = Path(runs_dir)
    out: list[RunMeta] = []
    for meta in runs_dir.glob("*/meta.yaml"):
        if meta.parent.name.startswith("_"):
            continue
        out.append(load_run(meta))
    return sorted(out, key=lambda r: r.id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_run_meta.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add erebor_site/run_meta.py tests/test_run_meta.py
git commit -m "feat: RunMeta pydantic schema + run loader"
```

---

## Task 3: Run data — template + run-0

**Files:**
- Create: `runs/_template/meta.yaml`
- Create: `runs/run-0/meta.yaml`
- Test: `tests/test_run_meta.py` (append a real-data test)

- [ ] **Step 1: Create the template** (`runs/_template/meta.yaml`)

```yaml
# Copy this directory to runs/<your-run-id>/ and fill it in.
# Required: id, status, description. Everything else is optional.
id: run-X                      # URL slug + display name, e.g. run-1
status: planned                # planned | running | complete | archived
description: >
  One or two sentences describing what this run was for.

date_begin: ""                 # e.g. 2026-06
date_end: ""

code:
  tag: ""                      # TAG_NAME, e.g. cdl1-run1
  phentax_version: ""          # e.g. 0.1.1b4
  code_link: ""

sources: []                    # e.g. [MBHB, GB, PSD]
dataset: ""                    # e.g. LDC Sangria / simulated
observation_time: ""           # e.g. "1 yr"

results:
  cluster_paths: []            # list of {host, path}
  cloud_urls: []

config: ""
contact: ""
plots: []                      # reserved for future figures
```

- [ ] **Step 2: Create run-0** (`runs/run-0/meta.yaml`)

```yaml
id: run-0
status: complete
description: >
  General development and testing of the global-fit infrastructure.

date_begin: "2026-05"
date_end: "2026-05"

code:
  tag: cdl1-run0
  phentax_version: 0.1.1b4
  code_link: https://github.com/Erebor-L2D/LISAanalysistools

sources: [PSD]
dataset: simulated
observation_time: ""

results:
  cluster_paths: []
  cloud_urls: []

config: ""
contact: ""
plots: []
```

- [ ] **Step 3: Append a real-data test to `tests/test_run_meta.py`**

```python
def test_repo_runs_all_valid():
    """Every committed runs/*/meta.yaml validates against RunMeta."""
    repo_runs = Path(__file__).resolve().parents[1] / "runs"
    loaded = load_runs(repo_runs)
    ids = [r.id for r in loaded]
    assert "run-0" in ids
    run0 = next(r for r in loaded if r.id == "run-0")
    assert run0.code.tag == "cdl1-run0"
    assert run0.sources == ["PSD"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_run_meta.py -q`
Expected: PASS (7 passed). The `_template` dir must be skipped (its `id: run-X` is still valid, but it lives under an underscore dir and is excluded).

- [ ] **Step 5: Commit**

```bash
git add runs/_template/meta.yaml runs/run-0/meta.yaml tests/test_run_meta.py
git commit -m "feat: add run template and run-0 (cdl1-run0) metadata"
```

---

## Task 4: Catalog renderer

**Files:**
- Create: `erebor_site/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_render.py`:
```python
from erebor_site.run_meta import RunMeta
from erebor_site.render import render_catalog


def _run(**kw):
    base = {"id": "run-0", "status": "complete", "description": "dev run"}
    base.update(kw)
    return RunMeta.model_validate(base)


def test_catalog_has_both_views_and_toggle():
    html = render_catalog([_run()])
    assert 'id="view-table"' in html
    assert 'id="view-cards"' in html
    assert "gfSetView('table')" in html
    assert "gfSetView('cards')" in html


def test_catalog_renders_run_fields():
    html = render_catalog([
        _run(code={"tag": "cdl1-run0"}, sources=["PSD", "MBHB"], dataset="simulated")
    ])
    assert 'href="runs/run-0/"' in html
    assert "cdl1-run0" in html
    assert "gf-done" in html            # complete -> green badge class
    assert ">PSD<" in html and ">MBHB<" in html
    assert "simulated" in html


def test_catalog_escapes_html():
    html = render_catalog([_run(description="<script>x</script>")])
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_render.py -q`
Expected: FAIL — `ImportError: cannot import name 'render_catalog'`.

- [ ] **Step 3: Implement `erebor_site/render.py` (catalog only for now)**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_render.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add erebor_site/render.py tests/test_render.py
git commit -m "feat: render_catalog (table + cards + toggle)"
```

---

## Task 5: Installation table renderer

**Files:**
- Modify: `erebor_site/render.py` (add `render_install_table`)
- Test: `tests/test_render.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_render.py`**

```python
from erebor_site.render import render_install_table


def test_install_table_has_header_and_rows():
    md = render_install_table([
        _run(code={"tag": "cdl1-run0", "phentax_version": "0.1.1b4"}),
    ])
    assert "| Run | TAG_NAME | PHENTAX_VERSION | Status |" in md
    assert "`cdl1-run0`" in md
    assert "`0.1.1b4`" in md
    assert "[run-0](runs/run-0.md)" in md


def test_install_table_handles_missing_fields():
    md = render_install_table([_run(id="run-9", status="planned")])
    # missing tag/version render as an em dash, never a crash
    assert "[run-9](runs/run-9.md)" in md
    assert "| `—` | `—` |" in md
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_render.py -q`
Expected: FAIL — `ImportError: cannot import name 'render_install_table'`.

- [ ] **Step 3: Append `render_install_table` to `erebor_site/render.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_render.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add erebor_site/render.py tests/test_render.py
git commit -m "feat: render_install_table (run -> version markdown)"
```

---

## Task 6: Run detail page renderer

**Files:**
- Modify: `erebor_site/render.py` (add `render_run_page`)
- Test: `tests/test_render.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_render.py`**

```python
from erebor_site.render import render_run_page


def test_run_page_includes_core_fields():
    md = render_run_page(_run(
        code={"tag": "cdl1-run0"},
        sources=["PSD"],
        dataset="simulated",
        contact="someone@example.com",
        results={"cluster_paths": [{"host": "hpc", "path": "/data/run0"}]},
    ))
    assert md.startswith("# run-0")
    assert "dev run" in md            # description
    assert "`cdl1-run0`" in md
    assert "PSD" in md
    assert "simulated" in md
    assert "someone@example.com" in md
    assert "/data/run0" in md


def test_run_page_no_results_message():
    md = render_run_page(_run())
    assert "No results recorded yet" in md
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_render.py -q`
Expected: FAIL — `ImportError: cannot import name 'render_run_page'`.

- [ ] **Step 3: Append `render_run_page` to `erebor_site/render.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_render.py -q`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add erebor_site/render.py tests/test_render.py
git commit -m "feat: render_run_page (per-run detail markdown)"
```

---

## Task 7: `from_metadata` converter

**Files:**
- Create: `erebor_site/from_metadata.py`
- Create: `tests/data/global_metadata.sample.json`
- Test: `tests/test_from_metadata.py`

- [ ] **Step 1: Create the fixture** (`tests/data/global_metadata.sample.json`)

This mirrors the non-underscore fields emitted by `RunMetadata.to_json()` (see `LISAanalysistools/.../postprocessing.py`):
```json
{
  "global_fit_version": "cdl1_run0",
  "global_fit_contact": "ereborl2d@googlegroups.com",
  "global_fit_code_link": "https://github.com/Erebor-L2D/LISAanalysistools",
  "input_reference": "LDC Sangria",
  "input_data_link": "/cluster/erebor/run0/input_data.h5",
  "submission_parent_folder": "/cluster/erebor/run0",
  "noise_model": "XYZSensitivityBackend",
  "comment": "First multi-source fit on Sangria.",
  "found_source_types_list": ["mbh", "gb", "psd"],
  "searched_source_types_list": ["mbh", "gb", "psd"],
  "observation_period_begin": "2026-06-01T000000",
  "observation_period_end": "2027-06-01T000000",
  "effective_observation_duration": "1 yr",
  "submission_timestamp": "2026-06-07T120000"
}
```

- [ ] **Step 2: Write the failing tests** (`tests/test_from_metadata.py`)

```python
import json
import yaml
from pathlib import Path

from erebor_site.run_meta import RunMeta
from erebor_site.from_metadata import derive_id, derive_tag, map_metadata, convert

SAMPLE = Path(__file__).parent / "data" / "global_metadata.sample.json"


def test_derive_id():
    assert derive_id("cdl1_run0") == "run-0"
    assert derive_id("run0") == "run-0"
    assert derive_id("weird") == "weird"


def test_derive_tag():
    assert derive_tag("cdl1_run0") == "cdl1-run0"


def test_map_metadata_core_fields():
    d = json.loads(SAMPLE.read_text())
    m = map_metadata(d)
    assert m["id"] == "run-0"
    assert m["tag"] == "cdl1-run0"
    assert m["sources"] == ["mbh", "gb", "psd"]
    assert m["dataset"] == "LDC Sangria"
    assert m["contact"] == "ereborl2d@googlegroups.com"
    assert m["observation_time"] == "1 yr"


def test_convert_writes_valid_yaml_with_todos(tmp_path):
    out = convert(SAMPLE, tmp_path)
    assert out == tmp_path / "run-0" / "meta.yaml"
    text = out.read_text()
    # TODO markers for fields not present in the JSON
    assert "# TODO" in text
    assert "phentax_version" in text
    # the generated draft must itself validate against the schema
    RunMeta.model_validate(yaml.safe_load(text))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_from_metadata.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'erebor_site.from_metadata'`.

- [ ] **Step 4: Implement `erebor_site/from_metadata.py`**

```python
"""Convert a global_metadata.json (RunMetadata.to_json) into a draft meta.yaml.

Pure JSON -> YAML; does not import LISAanalysistools. Fields absent from the JSON
(status, phentax_version, cloud_urls) are written with `# TODO` markers for the
author to complete before opening a PR.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from .run_meta import RunMeta


def derive_id(global_fit_version: str) -> str:
    """'cdl1_run0' -> 'run-0' (part after first '_', hyphen before trailing digits)."""
    part = global_fit_version.split("_", 1)[1] if "_" in global_fit_version else global_fit_version
    m = re.fullmatch(r"([a-zA-Z]+)(\d+)", part)
    return f"{m.group(1)}-{m.group(2)}" if m else part


def derive_tag(global_fit_version: str) -> str:
    """'cdl1_run0' -> 'cdl1-run0' (matches installation.md TAG_NAME)."""
    return global_fit_version.replace("_", "-")


def map_metadata(d: dict) -> dict:
    """Map the global_metadata.json dict to the fields we can fill automatically."""
    gfv = d.get("global_fit_version", "") or ""
    sources = d.get("found_source_types_list") or d.get("searched_source_types_list") or []
    return {
        "id": derive_id(gfv) if gfv else "",
        "tag": derive_tag(gfv) if gfv else "",
        "code_link": d.get("global_fit_code_link", "") or "",
        "sources": list(sources),
        "dataset": d.get("input_reference", "") or "",
        "observation_time": d.get("effective_observation_duration", "") or "",
        "date_begin": d.get("observation_period_begin", "") or d.get("submission_timestamp", "") or "",
        "date_end": d.get("observation_period_end", "") or "",
        "contact": d.get("global_fit_contact", "") or "",
        "description": d.get("comment", "") or "TODO: describe this run",
        "config": d.get("noise_model", "") or "",
        "cluster_path": d.get("input_data_link", "") or d.get("submission_parent_folder", "") or "",
    }


def _j(value: str) -> str:
    """JSON-encode a scalar so it is always valid YAML (handles quotes/specials)."""
    return json.dumps(value)


def to_yaml(m: dict) -> str:
    """Render an annotated draft meta.yaml (with TODO comments) from mapped fields."""
    return f"""\
id: {m['id']}
status: complete            # TODO: confirm (planned | running | complete | archived)
description: {_j(m['description'])}

date_begin: {_j(m['date_begin'])}
date_end: {_j(m['date_end'])}

code:
  tag: {_j(m['tag'])}
  phentax_version: ""        # TODO: not in global_metadata.json
  code_link: {_j(m['code_link'])}

sources: {json.dumps(m['sources'])}
dataset: {_j(m['dataset'])}
observation_time: {_j(m['observation_time'])}

results:
  cluster_paths:
    - host: "TODO-host"      # TODO: which machine
      path: {_j(m['cluster_path'])}
  cloud_urls: []             # TODO: add cloud URLs if any

config: {_j(m['config'])}
contact: {_j(m['contact'])}
plots: []
"""


def convert(json_path: Path, out_dir: Path = Path("runs")) -> Path:
    """Read global_metadata.json, write a validated draft runs/<id>/meta.yaml."""
    d = json.loads(Path(json_path).read_text())
    m = map_metadata(d)
    yaml_text = to_yaml(m)
    RunMeta.model_validate(yaml.safe_load(yaml_text))  # fail loudly if the draft is invalid
    out = Path(out_dir) / m["id"] / "meta.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml_text)
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Draft a runs/<id>/meta.yaml from a global_metadata.json file.",
    )
    parser.add_argument("json_path", type=Path, help="path to global_metadata.json")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("runs"))
    args = parser.parse_args(argv)
    out = convert(args.json_path, args.out_dir)
    print(f"Wrote {out}  — review the # TODO fields before committing.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_from_metadata.py -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Smoke-test the CLI**

Run: `uv run python -m erebor_site.from_metadata tests/data/global_metadata.sample.json -o /tmp/erebor_runs`
Expected: prints `Wrote /tmp/erebor_runs/run-0/meta.yaml  — review the # TODO fields before committing.`

- [ ] **Step 7: Commit**

```bash
git add erebor_site/from_metadata.py tests/test_from_metadata.py tests/data/global_metadata.sample.json
git commit -m "feat: from_metadata converter (global_metadata.json -> draft meta.yaml)"
```

---

## Task 8: Front-end assets (toggle CSS + JS)

**Files:**
- Create: `docs/assets/catalog.css`
- Create: `docs/assets/catalog.js`

- [ ] **Step 1: Create `docs/assets/catalog.css`**

```css
/* Status badges */
.gf-badge { display:inline-block; padding:2px 8px; border-radius:10px;
  font-size:11px; font-weight:600; color:#fff; }
.gf-done { background:#2e7d32; }
.gf-run  { background:#1565c0; }
.gf-plan { background:#777; }
.gf-arch { background:#9c5700; }

/* Source chips */
.gf-chip { display:inline-block; padding:1px 7px; margin:1px; border-radius:8px;
  font-size:11px; background:var(--md-default-fg-color--lightest); }

/* Toolbar / toggle */
.gf-toolbar { display:flex; gap:8px; align-items:center; margin:10px 0 14px; }
.gf-label { font-size:13px; opacity:.7; }
.gf-toggle { display:inline-flex; border:1px solid var(--md-default-fg-color--lighter);
  border-radius:8px; overflow:hidden; }
.gf-toggle button { border:0; background:transparent; padding:6px 16px; font-size:13px;
  font-weight:600; cursor:pointer; color:var(--md-default-fg-color--light); }
.gf-toggle button.active { background:var(--md-primary-fg-color); color:#fff; }

/* Table */
.gf-tbl { width:100%; border-collapse:collapse; font-size:13px; }
.gf-tbl th { text-align:left; padding:6px 8px; font-size:11px; text-transform:uppercase;
  opacity:.7; border-bottom:2px solid var(--md-default-fg-color--lighter); }
.gf-tbl td { padding:6px 8px; vertical-align:top;
  border-bottom:1px solid var(--md-default-fg-color--lightest); }
.gf-sub { font-size:11px; opacity:.6; }
.gf-rpath { cursor:help; text-decoration:underline dotted; }

/* Cards */
.gf-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }
.gf-card { border:1px solid var(--md-default-fg-color--lighter); border-radius:10px; padding:12px; }
.gf-card h4 { margin:0 0 4px 0; font-size:15px; }
.gf-meta { font-size:11px; opacity:.6; margin:2px 0 6px; }
.gf-desc { font-size:13px; margin:6px 0; }
.gf-links { font-size:12px; }

.gf-hidden { display:none; }
```

- [ ] **Step 2: Create `docs/assets/catalog.js`**

```javascript
// Toggle the runs catalog between table and cards; remember the choice.
function gfSetView(v) {
  document.querySelectorAll('.gf-view').forEach(function (el) {
    el.classList.toggle('gf-hidden', el.id !== 'view-' + v);
  });
  var bt = document.getElementById('gf-btn-table');
  var bc = document.getElementById('gf-btn-cards');
  if (bt) bt.classList.toggle('active', v === 'table');
  if (bc) bc.classList.toggle('active', v === 'cards');
  try { localStorage.setItem('gf-view', v); } catch (e) {}
}
window.gfSetView = gfSetView;

document.addEventListener('DOMContentLoaded', function () {
  var saved = null;
  try { saved = localStorage.getItem('gf-view'); } catch (e) {}
  if (saved === 'cards' || saved === 'table') gfSetView(saved);
});
```

- [ ] **Step 3: Commit**

```bash
git add docs/assets/catalog.css docs/assets/catalog.js
git commit -m "feat: catalog toggle styling and behavior"
```

---

## Task 9: MkDocs config, pages, and hook wiring

**Files:**
- Create: `mkdocs.yml`
- Create: `hooks.py`
- Create: `docs/index.md`
- Create: `docs/adding-a-run.md`
- Create: `docs/installation.md` (from the existing repo-root `installation.md`)

- [ ] **Step 1: Create `mkdocs.yml`**

```yaml
site_name: Erebor global-fit runs
site_description: Catalog of Erebor LISA global-fit runs, sources, and results.
site_url: https://erebor-l2d.github.io/Erebor-tools/

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle: { icon: material/weather-night, name: Switch to dark mode }
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle: { icon: material/weather-sunny, name: Switch to light mode }
  features:
    - navigation.sections
    - content.code.copy
    - search.highlight

nav:
  - Home: index.md
  - Installation: installation.md
  - Adding a run: adding-a-run.md

hooks:
  - hooks.py

extra_css:
  - assets/catalog.css
extra_javascript:
  - assets/catalog.js

markdown_extensions:
  - admonition
  - attr_list
  - md_in_html
  - tables
  - pymdownx.superfences
  - pymdownx.highlight

validation:
  nav:
    omitted_files: ignore        # generated run pages are reached via the catalog
  links:
    not_found: warn

exclude_docs: |
  superpowers/                   # planning specs/plans live under docs/ but are NOT published as site pages
```

- [ ] **Step 2: Create `hooks.py`** (thin MkDocs adapter — no rendering logic here)

```python
"""MkDocs hooks: generate per-run pages and inject the catalog + install table.

All rendering lives in erebor_site.render; this module only wires it into the
build. Run metadata is read from the repo-root runs/ directory.
"""
from __future__ import annotations

from pathlib import Path

from mkdocs.structure.files import File

from erebor_site.render import render_catalog, render_install_table, render_run_page
from erebor_site.run_meta import load_runs

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
    """Replace {{ catalog }} on Home and {{ install_table }} on Installation."""
    src = page.file.src_uri
    if src == "index.md" and "{{ catalog }}" in markdown:
        markdown = markdown.replace("{{ catalog }}", render_catalog(_runs()))
    elif src == "installation.md" and "{{ install_table }}" in markdown:
        markdown = markdown.replace("{{ install_table }}", render_install_table(_runs()))
    return markdown
```

- [ ] **Step 3: Create `docs/index.md`**

```markdown
# Erebor global-fit runs

Welcome to the **Erebor** global-fit runs catalog. Each run records the sources
included, the code versions used, and where to find the results. See
[Installation](installation.md) to set up the code for a given run, and
[Adding a run](adding-a-run.md) to register a new one.

## Runs

{{ catalog }}
```

- [ ] **Step 4: Create `docs/adding-a-run.md`**

```markdown
# Adding a run

Runs are described by one `meta.yaml` per run under `runs/<id>/`. That file is the
single source of truth — the catalog, the run's detail page, and the installation
table are all generated from it.

## Option A — from a finished run's metadata (recommended)

A completed global fit writes a `global_metadata.json` into its submission folder.
Turn it into a draft entry:

```bash
uv run python -m erebor_site.from_metadata /path/to/global_metadata.json
```

This writes `runs/<id>/meta.yaml` with everything it could infer and `# TODO`
markers for the fields that are not in the JSON (`status`, `phentax_version`,
cloud URLs, the cluster host). Fill those in.

## Option B — by hand

Copy the template and edit it:

```bash
cp -r runs/_template runs/run-N
$EDITOR runs/run-N/meta.yaml
```

## Validate, preview, and open a PR

```bash
uv run pytest -q              # schema validation of all runs
uv run mkdocs serve          # preview at http://127.0.0.1:8000
```

Then commit `runs/<id>/meta.yaml` and open a pull request. CI validates every
`meta.yaml` and builds the site.
```

- [ ] **Step 5: Create `docs/installation.md` from the existing file**

Copy the repo-root `installation.md` into `docs/installation.md`, then replace the
run→version block (the `## TAG_NAME and PHENTAX_VERSION` heading and the `**run 0**`
… `**run 5**` lines) with a placeholder. Concretely, that section becomes:

```markdown
## TAG_NAME and PHENTAX_VERSION
We provide a mapping between the global fit runs and the code versions below.
Each run links to its full details.

{{ install_table }}
```

Leave the rest of the file (Prerequisites, Installation steps, etc.) unchanged.

Run: `cp installation.md docs/installation.md`
Then edit `docs/installation.md` to apply the replacement above.

- [ ] **Step 6: Build the site and verify generation (the integration check)**

Run: `uv run mkdocs build --strict`
Expected: build succeeds with no warnings (──strict turns warnings into errors).

Run: `test -f site/runs/run-0/index.html && echo PAGE_OK`
Expected: `PAGE_OK` (the per-run page was generated).

Run: `grep -q "gfSetView" site/index.html && grep -q "cdl1-run0" site/index.html && echo CATALOG_OK`
Expected: `CATALOG_OK` (the catalog was injected into Home).

Run: `grep -q 'href="../runs/run-0/"' site/installation/index.html && echo LINK_OK`
Expected: `LINK_OK` — the install table was injected **and** its run link resolved to the correct page-relative path (asserting the href, not just the tag text, is what distinguishes a working link from a broken one).

- [ ] **Step 7: Verify the toggle interactively (one-time manual check)**

Run: `uv run mkdocs serve`
Open `http://127.0.0.1:8000`, confirm the **Table/Cards** toggle switches views and
the choice survives a page reload. Stop the server with Ctrl-C.

- [ ] **Step 8: Commit**

```bash
git add mkdocs.yml hooks.py docs/index.md docs/adding-a-run.md docs/installation.md
git commit -m "feat: mkdocs config, pages, and run/catalog/table generation hooks"
```

---

## Task 10: GitHub Actions deploy + README pointer

**Files:**
- Create: `.github/workflows/docs.yml`
- Modify: `README.md` (add a site link + note)

- [ ] **Step 1: Create `.github/workflows/docs.yml`**

```yaml
name: docs

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Build site
        run: uv run mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

The PR job builds (catching broken runs/build before merge); deploy runs only on `main`.

- [ ] **Step 2: Add a site pointer to `README.md`**

Append to `README.md`:
```markdown

## Runs catalog
A browsable catalog of global-fit runs (sources, code versions, where to find
results) is published from this repo via GitHub Pages. See [`docs/`](./docs) and
the [Adding a run](./docs/adding-a-run.md) guide.
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/docs.yml README.md
git commit -m "ci: build + deploy docs to GitHub Pages"
```

- [ ] **Step 4: Manual post-merge steps (cannot be scripted here — do via GitHub UI)**

1. Make the `Erebor-L2D/Erebor-tools` repo **public** (Settings → General → Danger Zone). Confirm nothing sensitive is committed first.
2. Settings → **Pages** → Source = **GitHub Actions**.
3. Push the branch / merge to `main`; the `docs` workflow deploys and prints the site URL.

---

## Self-Review

**Spec coverage** (against `2026-06-07-erebor-tools-runs-site-design.md`):
- IA — Home/Runs/Installation/Adding-a-run → Tasks 9 (pages) + 6/4 (run pages, catalog). ✅
- `RunMeta` pydantic + one `meta.yaml` per run → Task 2/3. ✅
- Generation pipeline (validate, run pages, catalog, install table) → Tasks 4/5/6 (renderers) + 9 (`hooks.py`). ✅
- Catalog table+cards toggle, default table, localStorage → Tasks 4 + 8. ✅
- Single source of truth (install table generated from `meta.yaml`) → Task 5 + 9 (installation.md placeholder). ✅
- `from_metadata` converter with TODO fields + underscore→hyphen normalization → Task 7. ✅
- Deployment via GitHub Actions to public Pages → Task 10. ✅
- Out of scope honored: no `gen_install.py` / per-run `pyproject.toml` / `install.sh`. ✅

**Placeholder scan:** No "TBD/implement later" in steps; every code step shows complete code; commands have expected output. The only `# TODO` strings are intentional output of the converter (Task 7) and the install draft is excluded. ✅

**Type consistency:** `RunMeta` fields (`code.tag`, `code.phentax_version`, `results.cluster_paths[].host/path`, `status` enum) are used identically across `render.py` (Tasks 4–6), `from_metadata.py` (Task 7), and `hooks.py` (Task 9). Renderers consume `RunMeta` objects; `hooks.py` calls `render_catalog`, `render_install_table`, `render_run_page`, `load_runs` exactly as defined. ✅

**Known soft spots (acceptable for MVP):**
- `File.generated` requires MkDocs ≥1.5; `mkdocs-material>=9.5` pulls a compatible MkDocs. If unavailable, Task 9 Step 6 build fails fast.
- Material "instant navigation" is **not** enabled, so the inline `onclick`/global `gfSetView` works without SPA re-init.
- **Link strategy:** the install table (Markdown) links `runs/<id>.md` so MkDocs computes the correct page-relative URL and `--strict` link validation passes from any page depth. The catalog (raw HTML) uses `<a href="runs/<id>/">`, which Python-Markdown stashes (not rewritten, not strict-validated) and is correct only from the root-depth Home page — the only page that embeds the catalog.
```
