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
