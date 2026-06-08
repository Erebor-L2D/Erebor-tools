# Erebor Full-Stack Install (per-run pyproject) — Design DRAFT

**Date:** 2026-06-07
**Status:** ⚠️ DRAFT — under discussion, NOT approved. Companion to the approved
`2026-06-07-erebor-tools-runs-site-design.md`. Do not implement until settled.
**Target repo:** `Erebor-L2D/Erebor-tools`

## Goal

Make the whole Erebor stack install declaratively, per run: each `runs/<id>/`
gets a `pyproject.toml` with PEP 508 git links pinning that run's exact code tags
(CPU + CUDA variants), generated from that run's `meta.yaml` (the site's single
source of truth).

## Open question (why this is still a draft)

Whether the per-run committed-and-generated `pyproject.toml` + `install.sh`
approach is the right shape, vs alternatives (uv-native `[tool.uv.sources]`, a
single bumpable root pyproject, or fixing versioning upstream). Decided so far
during brainstorming: PEP 508 git URLs (pip-compatible), per-run granularity,
`cpu`/`cuda12`/`cuda13` extras, `lisa-on-gpu` from the personal fork for now.
User has flagged they are **not yet sure** about the setup.

## Findings from upstream build configs

- Every package declares `build-system.requires`, so build isolation works —
  `--no-build-isolation` in the old `installation.md` was an optimization, not a
  hard requirement (at least for CPU).
- `GPUBackendTools`, `LISAanalysistools`, `lisa-on-gpu`, `GBGPU` derive version
  from the git tag via setuptools_scm. A non-PEP440 tag like `cdl1-run0` fails the
  build unless `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_<DIST>` is set (LISAanalysistools
  needs a high pretend version, 2.0.0, to satisfy downstream mins).
- `LISAanalysistools` pulls `mojito-processor` from testpypi; `phentax` is on
  testpypi too. A consumer pyproject must declare that index itself — dependency
  `[tool.uv.sources]`/indexes do **not** propagate from a git dep.
- `Eryn` has a static version + `uv_build` backend, branch `gf-dev`. `bbhx` is
  plain pypi.

## Proposed per-run `pyproject.toml` (generated, committed)

Dependency-only metapackage. The explicit `[build-system]` is required because
installing an *extra* forces pip to build the project's metadata (without it,
setuptools auto-discovery scans the run dir, finds no Python package, and
errors/warns).

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "erebor-stack-run-0"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
  "eryn @ git+https://github.com/Erebor-L2D/Eryn.git@gf-dev",
  "gpubackendtools @ git+https://github.com/Erebor-L2D/GPUBackendTools.git@cdl1-run0",
  "lisaanalysistools @ git+https://github.com/Erebor-L2D/LISAanalysistools.git@cdl1-run0",
  "fastlisaresponse @ git+https://github.com/asantini29/lisa-on-gpu.git@cdl1-run0",  # TODO: Erebor-L2D fork
  "gbgpu @ git+https://github.com/Erebor-L2D/GBGPU.git@cdl1-run0",
  "bbhx",
  "mojito",
]

[project.optional-dependencies]
cpu    = ["phentax[cpu]==0.1.1b4"]                      # cpu = no cupy
cuda12 = ["cupy-cuda12x", "phentax[cuda12]==0.1.1b4"]
cuda13 = ["cupy-cuda13x", "phentax[cuda13]==0.1.1b4"]

[tool.setuptools]
py-modules = []        # explicit: dependency-only metapackage, no code to discover
```

**Mandatory variant.** `phentax` is declared only inside the extras, so a no-extra
install would silently omit the MBHB waveform generator. `install.sh` therefore
**requires** a variant argument and errors if none is given.

## Install frictions, handled explicitly

PEP 508 URLs cannot carry indexes or env vars, so each run dir also gets a
generated `install.sh` (the run page documents the equivalent one-liner):

1. **setuptools_scm + non-PEP440 tags** → export
   `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_LISAANALYSISTOOLS=2.0.0`,
   `…_GPUBACKENDTOOLS=0.1.0`, `…_FASTLISARESPONSE=0.1.0`, `…_GBGPU=0.1.0`.
2. **testpypi packages** (`mojito-processor`, `phentax`) →
   `--extra-index-url https://test.pypi.org/simple/`.
3. Resulting command, e.g.:
   ```bash
   bash runs/run-0/install.sh cuda12     # wraps env + extra-index-url; variant arg required
   # equivalently (note the ./ prefix so pip treats it as a path, not a req name):
   pip install --extra-index-url https://test.pypi.org/simple/ "./runs/run-0[cuda12]"
   ```

**Proper long-term fix (upstream, out of scope):** add `fallback_version` to each
package's `[tool.setuptools_scm]` so non-version tags build without the
pretend-version env vars — would make `install.sh` unnecessary.

## Generation + structure (if approved)

- `erebor_site/gen_install.py`: `meta.yaml` → `runs/<id>/pyproject.toml` + `install.sh`.
- `from_metadata` also regenerates these after writing a draft `meta.yaml`.
- `hooks.py` drift check: verify each committed `pyproject.toml` matches what
  `gen_install.py` would emit; fail the build if stale.

## Honest limitations

- **System prerequisites remain**: CMake, a C++ compiler, and (GPU) the matching
  CUDA toolkit on `PATH`. "Fully pip installable" ≠ "zero system setup".
- **CI does not install-test** the generated pyproject — the docs workflow builds
  mkdocs; the drift check only confirms the file matches the generator. A
  deterministically-generated-but-broken file passes every automated gate until a
  human runs it.

## Verify early (before building `gen_install.py`)

- Confirm per-distribution `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_<DIST>` propagates
  through `scikit_build_core.metadata.setuptools_scm` in an isolated build — test
  one package (e.g. `gpubackendtools`) with a non-PEP440 tag.
- Confirm Eryn's `uv_build` PEP 517 backend installs via plain pip.
- Confirm `pip install "./runs/run-0[cuda12]"` (path + extra) resolves with the
  `[build-system]` present.
```
