"""Run metadata schema (the single source of truth for each global-fit run)."""
from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    planned = "planned"
    running = "running"
    complete = "complete"
    archived = "archived"


class ClusterPath(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str
    path: str


class Results(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cluster_paths: list[ClusterPath] = Field(default_factory=list)
    cloud_urls: list[str] = Field(default_factory=list)


class SourceDetail(BaseModel):
    """Per-source-type metadata shown on a run's detail page."""

    model_config = ConfigDict(extra="forbid")
    type: str
    n_found: int | None = None
    waveform_model: str | None = None
    waveform_model_link: str | None = None
    freq_min: float | None = None
    freq_max: float | None = None
    n_bands: int | None = None
    prior_link: str | None = None
    n_posteriors: int | None = None
    noise_model: str | None = None  # only for the NOISE entry


class RunMeta(BaseModel):
    """Validated metadata for one global-fit run."""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: str | None = None  # iteration of this run, e.g. v3
    erebortools_version: str | None = None  # erebortools release pinning the stack, e.g. v0.1.0
    status: Status
    description: str
    date: str | None = None  # date the run was performed (YYYY-MM-DD)

    # analysis configuration
    domain: str | None = None  # frequency | time | time-frequency
    start_freq_hz: float | None = None
    end_freq_hz: float | None = None
    sampling_frequency_hz: float | None = None
    observation_time: str | None = None

    dataset: str | None = None
    sources: list[str] = Field(default_factory=list)  # high-level chips
    source_details: list[SourceDetail] = Field(default_factory=list)

    results: Results = Field(default_factory=Results)
    config: str | None = None
    contact: str | None = None
    plots: list = Field(default_factory=list)


def load_run(path: Path) -> RunMeta:
    """Load and validate a single meta.yaml, raising ValueError naming the file."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text()) or {}
        return RunMeta.model_validate(data)
    except Exception as exc:  # noqa: BLE001 - re-raise with file context
        label = "/".join(path.parts[-2:])
        raise ValueError(f"Invalid run metadata in {label}: {exc}") from exc


def _version_sort_key(version: str | None) -> tuple[int, int, str]:
    """Order unversioned runs first, then by numeric version (v3 < v4 < v10)."""
    if not version:
        return (0, 0, "")
    m = re.search(r"\d+", version)
    return (1, int(m.group()) if m else 0, version)


def load_runs(runs_dir: Path) -> list[RunMeta]:
    """Load every runs/*/meta*.yaml (skipping _underscore dirs).

    A run directory may hold several versioned files (meta_v3.yaml,
    meta_v4.yaml, ...); each is loaded as its own RunMeta so every version
    of a run shows up in the catalog. Sorted by (id, version).
    """
    runs_dir = Path(runs_dir)
    out: list[RunMeta] = []
    for meta in runs_dir.glob("*/meta*.yaml"):
        if meta.parent.name.startswith("_"):
            continue
        out.append(load_run(meta))
    return sorted(out, key=lambda r: (r.id, _version_sort_key(r.version)))


def run_page_slug(run: RunMeta) -> str:
    """Docs-relative page path (no extension) for one run version.

    Versions nest under the run: 'run-1/v3' -> URL runs/run-1/v3/.
    Unversioned runs stay flat: 'run-1' -> URL runs/run-1/. This is the single
    source of truth shared by the page generator (hooks) and the catalog links.
    """
    return f"{run.id}/{run.version}" if run.version else run.id
