"""Convert global_metadata.json (+ sibling per-source JSONs) into a draft meta.yaml.

Pure JSON -> YAML; does not import LISAanalysistools. `status`, cluster host, and
cloud URLs are left for the author to complete (see the TODO header it writes).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from .run_meta import RunMeta

_DOMAIN_LABELS = {
    "FDSettings": "frequency",
    "TDSettings": "time",
    "STFTSettings": "time-frequency",
    "WDMSettings": "time-frequency",
}


def derive_id(global_fit_version: str) -> str:
    """Best-effort run id: 'CDL1run1_v3' -> 'run-1', 'cdl1_run0' -> 'run-0'."""
    m = re.search(r"run[_-]?(\d+)", global_fit_version, re.IGNORECASE)
    if m:
        return f"run-{int(m.group(1))}"
    part = global_fit_version.split("_", 1)[1] if "_" in global_fit_version else global_fit_version
    m2 = re.fullmatch(r"([a-zA-Z]+)(\d+)", part)
    return f"{m2.group(1)}-{m2.group(2)}" if m2 else part


def _domain_label(d: dict) -> str | None:
    cls = (d.get("domain_metadata") or {}).get("class", "")
    return _DOMAIN_LABELS.get(cls, cls) or None


def _seconds_human(sec: float) -> str:
    days = sec / 86400.0
    return f"{days / 365.25:.2f} yr" if days >= 365 else f"{days:.1f} days"


def _load_source_file(path: Path) -> dict:
    sd = json.loads(path.read_text())
    fr = sd.get("frequency_ranges") or []
    flat = [x for rng in fr for x in rng]
    unique_posteriors = list(dict.fromkeys(sd.get("posterior_files") or []))
    n_found = len(sd.get("detection_statistic") or []) or len(unique_posteriors) or None
    return {
        "type": str(sd.get("source_type", "")).upper(),
        "n_found": n_found,
        "waveform_model": sd.get("waveform_model") or None,
        "waveform_model_link": sd.get("waveform_model_code_link") or None,
        "freq_min": min(flat) if flat else None,
        "freq_max": max(flat) if flat else None,
        "n_bands": len(fr) or None,
        "prior_link": sd.get("prior_model_code_link") or None,
        "n_posteriors": len(unique_posteriors) or None,
    }


def _discover_source(folder: Path, source_type: str) -> dict | None:
    matches = sorted(
        m for m in folder.glob(f"*_{source_type}_*.json") if m.name != "global_metadata.json"
    )
    return _load_source_file(matches[-1]) if matches else None  # latest by name


def map_metadata(d: dict, folder: Path) -> dict:
    gfv = d.get("global_fit_version", "") or ""
    found = d.get("found_source_types_list") or d.get("searched_source_types_list") or []
    kw = (d.get("domain_metadata") or {}).get("kwargs") or {}
    ts = d.get("time_step")
    fs = (1.0 / ts) if ts else None
    tobs = (d.get("preprocessing_metadata") or {}).get("Tobs")

    source_details: list[dict] = []
    for st in found:
        if str(st).upper() == "NOISE":
            source_details.append(
                {
                    "type": "NOISE",
                    "noise_model": d.get("noise_model") or None,
                    "prior_link": d.get("noise_model_code_link") or None,
                }
            )
            continue
        sd = _discover_source(folder, str(st).upper())
        source_details.append(sd if sd is not None else {"type": str(st).upper()})

    return {
        "id": derive_id(gfv) if gfv else "",
        "domain": _domain_label(d),
        "start_freq_hz": kw.get("min_freq"),
        "end_freq_hz": kw.get("max_freq"),
        "sampling_frequency_hz": fs,
        "observation_time": _seconds_human(tobs) if tobs else (d.get("effective_observation_duration") or None),
        "dataset": d.get("input_reference") or None,
        "date": (d.get("submission_timestamp") or "").split("T")[0] or None,
        "contact": d.get("global_fit_contact") or None,
        "description": d.get("comment") or "TODO: describe this run",
        "config": d.get("noise_model") or None,
        "sources": [str(s).upper() for s in found],
        "source_details": source_details,
        "cluster_path": d.get("input_data_link") or d.get("submission_parent_folder") or "",
    }


def build_meta(m: dict) -> dict:
    """Assemble the ordered meta.yaml dict (status defaults to complete)."""
    return {
        "id": m["id"],
        "status": "complete",
        "description": m["description"],
        "date": m["date"],
        "domain": m["domain"],
        "start_freq_hz": m["start_freq_hz"],
        "end_freq_hz": m["end_freq_hz"],
        "sampling_frequency_hz": m["sampling_frequency_hz"],
        "observation_time": m["observation_time"],
        "dataset": m["dataset"],
        "sources": m["sources"],
        "source_details": m["source_details"],
        "results": {
            "cluster_paths": [{"host": "TODO-host", "path": m["cluster_path"]}],
            "cloud_urls": [],
        },
        "config": m["config"],
        "contact": m["contact"],
        "plots": [],
    }


_TODO_HEADER = (
    "# TODO: review this draft before committing.\n"
    "#   - confirm `status` (planned | running | complete | archived)\n"
    "#   - set results.cluster_paths[].host and add cloud_urls if any\n\n"
)


def convert(json_path, out_dir=Path("runs")) -> Path:
    """Read global_metadata.json (+ sibling source files), write a validated draft."""
    json_path = Path(json_path)
    d = json.loads(json_path.read_text())
    m = map_metadata(d, json_path.parent)
    meta = build_meta(m)
    RunMeta.model_validate(meta)  # fail loudly if the draft is invalid
    text = _TODO_HEADER + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    out = Path(out_dir) / m["id"] / "meta.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Draft a runs/<id>/meta.yaml from a global_metadata.json (+ sibling per-source JSONs).",
    )
    parser.add_argument("json_path", type=Path, help="path to global_metadata.json")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("runs"))
    args = parser.parse_args(argv)
    out = convert(args.json_path, args.out_dir)
    print(f"Wrote {out}  — review the # TODO fields before committing.")


if __name__ == "__main__":
    main()
