from erebortools.website.run_meta import RunMeta
from erebortools.website.render import render_catalog, render_run_page


def _run(**kw):
    base = {"id": "run-1", "status": "complete", "description": "dev run"}
    base.update(kw)
    return RunMeta.model_validate(base)


def test_catalog_has_both_views_and_toggle():
    html = render_catalog([_run()])
    assert 'id="view-table"' in html
    assert 'id="view-cards"' in html
    assert "gfSetView('table')" in html
    assert "gfSetView('cards')" in html


def test_catalog_renders_run_fields():
    html = render_catalog([_run(sources=["MBHB", "GB"], dataset="mojito light", version="v3", erebortools_version="v0.1.0")])
    assert 'href="runs/run-1/v3/"' in html  # versioned runs nest under the run id
    assert "gf-done" in html
    assert ">MBHB<" in html and ">GB<" in html
    assert "mojito light" in html
    assert "<th>Version</th>" in html
    assert ">v3<" in html
    assert "<th>erebortools</th>" in html
    assert "releases/tag/v0.1.0" in html


def test_catalog_unversioned_run_links_flat():
    html = render_catalog([_run()])  # no version -> page stays at runs/<id>/
    assert 'href="runs/run-1/"' in html


def test_catalog_escapes_html():
    html = render_catalog([_run(description="<script>x</script>")])
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_run_page_has_analysis_and_sources():
    md = render_run_page(_run(
        version="v3",
        erebortools_version="v0.1.0",
        domain="frequency",
        start_freq_hz=0.0001,
        end_freq_hz=0.029,
        sampling_frequency_hz=0.2,
        observation_time="0.75 yr",
        sources=["MBHB", "NOISE"],
        source_details=[
            {"type": "MBHB", "n_found": 6, "waveform_model": "PhenomTHMTDIWaveform",
             "waveform_model_link": "https://example.org/wf", "freq_min": 0.0001,
             "freq_max": 0.029, "n_bands": 1, "prior_link": "https://example.org/prior",
             "n_posteriors": 6},
            {"type": "NOISE", "noise_model": "parametric"},
        ],
    ))
    assert md.startswith("# run-1 · v3")  # heading carries the version
    assert "## Analysis" in md
    assert "**Domain:** frequency" in md
    assert "Start frequency:" in md and "0.0001 Hz" in md
    assert "Sampling frequency:" in md and "0.2 Hz" in md
    assert "## Sources" in md
    assert "### MBHB" in md
    assert "Sources found:** 6" in md
    assert "[PhenomTHMTDIWaveform](https://example.org/wf)" in md
    assert "### NOISE" in md
    assert "Noise model:** parametric" in md
    assert "**Version:** v3" in md
    assert "**erebortools:** [v0.1.0]" in md


def test_run_page_no_results_message():
    md = render_run_page(_run())
    assert "No results recorded yet" in md
