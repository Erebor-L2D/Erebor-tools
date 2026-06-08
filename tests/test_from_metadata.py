import yaml
from pathlib import Path

from erebortools.website.run_meta import RunMeta
from erebortools.website.from_metadata import derive_id, map_metadata, convert

EXAMPLE = Path(__file__).resolve().parents[1] / "example"
SAMPLE = EXAMPLE / "global_metadata.json"


def test_derive_id():
    assert derive_id("cdl1_run0") == "run-0"
    assert derive_id("CDL1run1_v3") == "run-1"
    assert derive_id("run0") == "run-0"
    assert derive_id("weird") == "weird"


def test_map_metadata_analysis_fields():
    import json
    d = json.loads(SAMPLE.read_text())
    m = map_metadata(d, EXAMPLE)
    assert m["id"] == "run-1"
    assert m["domain"] == "frequency"
    assert m["start_freq_hz"] == 0.0001
    assert m["end_freq_hz"] == 0.029
    assert abs(m["sampling_frequency_hz"] - 0.2) < 1e-9
    assert m["dataset"] == "mojito light"
    assert set(m["sources"]) == {"MBHB", "GB", "NOISE"}


def test_map_metadata_source_details():
    import json
    d = json.loads(SAMPLE.read_text())
    sd = {s["type"]: s for s in map_metadata(d, EXAMPLE)["source_details"]}
    assert sd["MBHB"]["n_found"] == 6
    assert sd["GB"]["n_found"] == 25
    assert sd["NOISE"]["noise_model"] == "parametric"


def test_convert_writes_valid_yaml(tmp_path):
    out = convert(SAMPLE, tmp_path)
    assert out == tmp_path / "run-1" / "meta.yaml"
    text = out.read_text()
    assert "# TODO" in text
    RunMeta.model_validate(yaml.safe_load(text))
