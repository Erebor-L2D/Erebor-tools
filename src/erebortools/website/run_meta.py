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
