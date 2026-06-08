# Erebor-tools Runs Site — Design Spec

**Date:** 2026-06-07
**Status:** Approved design, pending implementation plan
**Target repo:** `Erebor-L2D/Erebor-tools` (currently at `results_misc/Erebor-tools`)

> The full-stack **install** design (per-run `pyproject.toml` with git links) is
> tracked separately in `2026-06-07-erebor-stack-pyproject-install-design.md`
> (DRAFT, under discussion) and is **not** part of this spec.

## Goal

A GitHub Pages website that serves as the catalog of Erebor global-fit runs. For
each run it shows what it was, which sources it included, the code versions used,
and where to find the results. Runs are described by structured YAML (one
`meta.yaml` per run) that is the single source of truth; the catalog, the per-run
detail pages, and the installation run→version table are all generated from it. A
converter turns a run's own emitted `global_metadata.json` into a draft run YAML
so runs self-register.

## Decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Audience | Collaborators + trusted external | Drives "no secrets on the page" |
| Visibility / deploy | **Make Erebor-tools public**; deploy via GitHub Actions → GitHub Pages | Simplest robust path; avoids private-Pages plan constraints |
| Build stack | MkDocs Material + YAML | Python/uv-native; existing `installation.md` drops in unchanged |
| Run data source | One `runs/<id>/meta.yaml` per run | Clean git diffs; per-run dir also holds future plots (+ install files later) |
| Schema validation | pydantic `RunMeta` model | On-brand with codebase; build fails on malformed runs |
| Catalog UI | Table + Cards toggle, **default Table**, choice remembered in `localStorage` | User asked for selectable view |
| Single source of truth | `meta.yaml` canonical; install run→version table generated from it | Avoids drift with `installation.md` |
| Auto-registration | `from_metadata` converter: `global_metadata.json` → draft `meta.yaml` | User requirement |

**Visibility consequence:** once the repo is public, everything committed
(cluster paths in run YAML, `installation.md`) is world-visible. Genuinely
sensitive credentials / host details must be kept out of committed files.

## Information architecture

MkDocs Material site with four areas:

- **Home** (`docs/index.md`) — short intro + the **runs catalog** (table/cards
  toggle, default table).
- **Runs** (`docs/runs/<id>.md`) — one auto-generated detail page per run: full
  schema, results pointers, and (future) plots.
- **Installation** (`docs/installation.md`) — existing content; the run→version
  table is **auto-generated** from `meta.yaml` (no hand-maintained duplicate).
- **Adding a run** (`docs/adding-a-run.md`) — contributor guide: run the
  converter (or copy the template), fill it, open a PR.

## Run data model — `RunMeta` (pydantic)

One `runs/<id>/meta.yaml` per run, validated by a pydantic `RunMeta` model.
Required: `id`, `status`, `description`. Everything else optional so planned/early
runs aren't blocked.

```yaml
# runs/run-0/meta.yaml
id: run-0                       # required; URL slug + display
status: complete               # required; planned | running | complete | archived
description: >                 # required
  General development and testing of the global-fit infrastructure.

date_begin: 2026-05
date_end: 2026-05

code:
  tag: cdl1-run0               # TAG_NAME (matches installation.md)
  phentax_version: 0.1.1b4     # PHENTAX_VERSION
  code_link: https://github.com/Erebor-L2D/LISAanalysistools

sources: [PSD]                 # chips: MBHB | GB | EMRI | foreground | PSD | ...
dataset: simulated             # input_reference
observation_time: ""           # effective_observation_duration, e.g. "1 yr"

results:
  cluster_paths:
    - host: <cluster>
      path: /path/on/cluster/...
  cloud_urls: []

config: ""                     # noise model / config file pointer
contact: ""                    # global_fit_contact
plots: []                      # FUTURE: figure paths/captions (door open)
```

The `plots` list is reserved now and rendered only when populated (keeps the
"plots later" door open with no rework). The per-run directory (`runs/<id>/`) is
also where those plots — and, later, the install files from the separate draft —
will live.

## Generation pipeline — `hooks.py`

A MkDocs build hook (native `hooks:` config, no exotic plugins):

1. Load every `runs/*/meta.yaml`, validate each via `RunMeta`. A validation error
   fails the build naming the file + field.
2. Generate `docs/runs/<id>.md` (one per run) from a template.
3. Inject the catalog (table HTML + cards HTML, both from the same data) into the
   Home page via a placeholder (e.g. `{{ catalog }}`).
4. Regenerate the installation run→version table from the same data.

Local preview: `uv run mkdocs serve`. Build: `uv run mkdocs build`.

## Catalog UI

Table (default) + Cards toggle, client-side, choice remembered in `localStorage`.
Status badges, source chips, results links. Both views fed from the same generated
data. (Validated visually during brainstorming.)

## Auto-registration — `from_metadata` converter

`erebor_site/from_metadata.py`, pure JSON→YAML (no LISAanalysistools import):

```
uv run python -m erebor_site.from_metadata path/to/global_metadata.json
# → writes runs/<id>/meta.yaml (draft)
```

Reads the `global_metadata.json` emitted by
`lisatools.globalfit.postprocessing.RunMetadata.to_json()` (written to the
submission folder as `global_metadata.json`, `postprocessing.py:1588`).

### Field mapping (`global_metadata.json` → `RunMeta`)

| JSON field | YAML target |
|---|---|
| `global_fit_version` (`"type_id"`) | `id` (id part) + `code.tag` (underscore→hyphen normalized) |
| `found_source_types_list` (fallback `searched_source_types_list`) | `sources` |
| `input_reference` | `dataset` |
| `input_data_link`, `submission_parent_folder` + folder name | `results.cluster_paths` |
| `effective_observation_duration` | `observation_time` |
| `observation_period_begin` / `_end` | `date_begin` / `date_end` |
| `submission_timestamp` | fallback date |
| `global_fit_contact` | `contact` |
| `global_fit_code_link` | `code.code_link` |
| `comment` | `description` |
| `noise_model`, `noise_model_config_file_link`, `preprocessing_metadata` | `config` |

### Fields not in the JSON → emitted as `# TODO`

- `status` (default suggestion `complete`, human confirms)
- `code.phentax_version` (not tracked in `RunMetadata`)
- `results.cloud_urls`
- `_web_extras` (nwalkers, ntemps, Tobs_s, …) — excluded from `to_dict()` (leading
  `_`), so absent from the JSON

Converter writes everything available + clearly-marked `# TODO: <field>`
placeholders. Output is a **draft** completed by the author via PR; `RunMeta`
validation gates the merge.

## Deployment

`.github/workflows/docs.yml`: on push to `main`, set up `uv`, install docs deps,
`uv run mkdocs build`, deploy to GitHub Pages (`actions/deploy-pages`). Repo made
public; Pages source = GitHub Actions.

## Repo structure (added to Erebor-tools)

```
mkdocs.yml
pyproject.toml                 # docs-site tooling (mkdocs-material, pydantic, pyyaml, pymdown-extensions)
hooks.py                       # validation + page/catalog/table generation
erebor_site/
  __init__.py
  run_meta.py                  # pydantic RunMeta model
  from_metadata.py             # global_metadata.json -> meta.yaml converter
runs/
  _template/meta.yaml          # copy-to-add template
  run-0/
    meta.yaml                  # real (cdl1-run0), single source of truth
docs/
  index.md                     # intro + {{ catalog }}
  installation.md              # version table auto-generated
  adding-a-run.md
  assets/
    catalog.css                # table/cards + badges/chips
    catalog.js                 # toggle + localStorage
.github/workflows/docs.yml
```

## Out of scope (future, door left open)

- **Full-stack per-run `pyproject.toml` install** — separate draft spec, under
  discussion; the per-run directory layout reserves a home for it.
- Per-run plots / figures on detail pages (`plots` field reserved; lives in
  `runs/<id>/plots/`).
- A cards "gallery" view once plots exist.
- Per-source detail (e.g. # GBs recovered, link to source catalog).
- Serializing `_web_extras` from `RunMetadata` to enrich auto-generated YAML.

## Prerequisites / risks

- **Make repo public** + enable Pages (source = GitHub Actions) — manual admin step.
- Cluster paths become public on publish — keep host/credential specifics out.
- `global_fit_version` must follow `type_id` for the converter to split id/tag;
  otherwise it falls back and flags a TODO.
```
