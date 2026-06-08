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
