# Adding a run

Runs are described by one `meta.yaml` per run under `runs/<id>/`. That file is the
single source of truth — the catalog, the run's detail page, and the installation
table are all generated from it.

## Option A — from a finished run's metadata (recommended)

A completed global fit writes a `global_metadata.json` into its submission folder.
Turn it into a draft entry:

```bash
uv run python -m erebortools.website.from_metadata /path/to/global_metadata.json
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
