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


def load_runs(runs_dir: Path) -> list[RunMeta]:
    """Load every runs/*/meta.yaml (skipping _underscore dirs), sorted by id."""
    runs_dir = Path(runs_dir)
    out: list[RunMeta] = []
    for meta in runs_dir.glob("*/meta.yaml"):
        if meta.parent.name.startswith("_"):
            continue
        out.append(load_run(meta))
    return sorted(out, key=lambda r: r.id)
