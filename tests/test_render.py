from erebor_site.run_meta import RunMeta
from erebor_site.render import render_catalog


def _run(**kw):
    base = {"id": "run-0", "status": "complete", "description": "dev run"}
    base.update(kw)
    return RunMeta.model_validate(base)


def test_catalog_has_both_views_and_toggle():
    html = render_catalog([_run()])
    assert 'id="view-table"' in html
    assert 'id="view-cards"' in html
    assert "gfSetView('table')" in html
    assert "gfSetView('cards')" in html


def test_catalog_renders_run_fields():
    html = render_catalog([
        _run(code={"tag": "cdl1-run0"}, sources=["PSD", "MBHB"], dataset="simulated")
    ])
    assert 'href="runs/run-0/"' in html
    assert "cdl1-run0" in html
    assert "gf-done" in html
    assert ">PSD<" in html and ">MBHB<" in html
    assert "simulated" in html


def test_catalog_escapes_html():
    html = render_catalog([_run(description="<script>x</script>")])
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
