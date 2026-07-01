import textwrap
import pytest
from pathlib import Path
from pydantic import ValidationError
from erebortools.website.run_meta import RunMeta, load_run, load_runs, run_page_slug


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))
    return path


def test_minimal_valid_applies_defaults():
    m = RunMeta.model_validate({"id": "run-0", "status": "complete", "description": "t"})
    assert m.id == "run-0"
    assert m.status.value == "complete"
    assert m.sources == []
    assert m.source_details == []
    assert m.domain is None
    assert m.results.cluster_paths == []


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate({"id": "x", "status": "finished", "description": "d"})


def test_missing_required_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate({"id": "x", "status": "complete"})


def test_unknown_key_rejected():
    with pytest.raises(ValidationError):
        RunMeta.model_validate({"id": "x", "status": "complete", "description": "d", "nope": 1})


def test_source_detail_validates():
    m = RunMeta.model_validate({
        "id": "x", "status": "complete", "description": "d",
        "source_details": [{"type": "MBHB", "n_found": 6}],
    })
    assert m.source_details[0].type == "MBHB"
    assert m.source_details[0].n_found == 6


def test_load_runs_skips_template_and_sorts(tmp_path):
    runs = tmp_path / "runs"
    _write(runs / "_template" / "meta.yaml", "id: tmpl\nstatus: planned\ndescription: t\n")
    _write(runs / "run-1" / "meta.yaml", "id: run-1\nstatus: running\ndescription: one\n")
    _write(runs / "run-0" / "meta.yaml", "id: run-0\nstatus: complete\ndescription: zero\n")
    assert [r.id for r in load_runs(runs)] == ["run-0", "run-1"]


def test_load_runs_loads_every_version_sorted(tmp_path):
    runs = tmp_path / "runs"
    _write(runs / "run-1" / "meta_v4.yaml", "id: run-1\nversion: v4\nstatus: complete\ndescription: four\n")
    _write(runs / "run-1" / "meta_v3.yaml", "id: run-1\nversion: v3\nstatus: complete\ndescription: three\n")
    _write(runs / "run-1" / "meta_v10.yaml", "id: run-1\nversion: v10\nstatus: complete\ndescription: ten\n")
    loaded = load_runs(runs)
    # every version shows up, sorted by numeric version (v10 after v4, not before)
    assert [r.version for r in loaded] == ["v3", "v4", "v10"]


def test_run_page_slug_nests_versions():
    versioned = RunMeta.model_validate({"id": "run-1", "version": "v3", "status": "complete", "description": "d"})
    unversioned = RunMeta.model_validate({"id": "run-1", "status": "complete", "description": "d"})
    assert run_page_slug(versioned) == "run-1/v3"
    assert run_page_slug(unversioned) == "run-1"


def test_load_run_error_names_file(tmp_path):
    bad = _write(tmp_path / "runs" / "bad" / "meta.yaml", "id: bad\nstatus: nope\ndescription: d\n")
    with pytest.raises(ValueError) as exc:
        load_run(bad)
    assert "bad/meta.yaml" in str(exc.value)


def test_repo_runs_all_valid():
    repo_runs = Path(__file__).resolve().parents[1] / "runs"
    loaded = load_runs(repo_runs)
    ids = [r.id for r in loaded]
    assert "run-1" in ids
    # both versioned files of run-1 load as separate entries
    versions = {r.version for r in loaded if r.id == "run-1"}
    assert {"v3", "v4"} <= versions
    run1_v3 = next(r for r in loaded if r.id == "run-1" and r.version == "v3")
    assert run1_v3.domain == "frequency"
    mbhb = next(s for s in run1_v3.source_details if s.type == "MBHB")
    assert mbhb.n_found == 6
