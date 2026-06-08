import json
import yaml
from pathlib import Path

from erebor_site.run_meta import RunMeta
from erebor_site.from_metadata import derive_id, derive_tag, map_metadata, convert

SAMPLE = Path(__file__).parent / "data" / "global_metadata.sample.json"


def test_derive_id():
    assert derive_id("cdl1_run0") == "run-0"
    assert derive_id("run0") == "run-0"
    assert derive_id("weird") == "weird"


def test_derive_tag():
    assert derive_tag("cdl1_run0") == "cdl1-run0"


def test_map_metadata_core_fields():
    d = json.loads(SAMPLE.read_text())
    m = map_metadata(d)
    assert m["id"] == "run-0"
    assert m["tag"] == "cdl1-run0"
    assert m["sources"] == ["mbh", "gb", "psd"]
    assert m["dataset"] == "LDC Sangria"
    assert m["contact"] == "ereborl2d@googlegroups.com"
    assert m["observation_time"] == "1 yr"


def test_convert_writes_valid_yaml_with_todos(tmp_path):
    out = convert(SAMPLE, tmp_path)
    assert out == tmp_path / "run-0" / "meta.yaml"
    text = out.read_text()
    assert "# TODO" in text
    assert "phentax_version" in text
    RunMeta.model_validate(yaml.safe_load(text))
