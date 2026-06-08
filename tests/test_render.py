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


from erebor_site.render import render_install_table


def test_install_table_has_header_and_rows():
    md = render_install_table([
        _run(code={"tag": "cdl1-run0", "phentax_version": "0.1.1b4"}),
    ])
    assert "| Run | TAG_NAME | PHENTAX_VERSION | Status |" in md
    assert "`cdl1-run0`" in md
    assert "`0.1.1b4`" in md
    assert "[run-0](runs/run-0.md)" in md


def test_install_table_handles_missing_fields():
    md = render_install_table([_run(id="run-9", status="planned")])
    assert "[run-9](runs/run-9.md)" in md
    assert "| `—` | `—` |" in md


from erebor_site.render import render_run_page


def test_run_page_includes_core_fields():
    md = render_run_page(_run(
        code={"tag": "cdl1-run0"},
        sources=["PSD"],
        dataset="simulated",
        contact="someone@example.com",
        results={"cluster_paths": [{"host": "hpc", "path": "/data/run0"}]},
    ))
    assert md.startswith("# run-0")
    assert "dev run" in md
    assert "`cdl1-run0`" in md
    assert "PSD" in md
    assert "simulated" in md
    assert "someone@example.com" in md
    assert "/data/run0" in md


def test_run_page_no_results_message():
    md = render_run_page(_run())
    assert "No results recorded yet" in md
