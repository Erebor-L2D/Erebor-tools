<!--
  Site/tooling changelog. Add new entries under "## [Unreleased]" as you work;
  on a release, rename that heading to the date (YYYY-MM-DD) and start a fresh
  [Unreleased] section. Group entries under Added / Changed / Fixed / Removed.
  This tracks the website and its tooling — not the science of individual runs.
-->
# Changelog

Notable changes to the Erebor-tools site. Dates are `YYYY-MM-DD`; format roughly
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## 2026-06-08

### Added
- Runs catalog with a Table/Cards toggle (the chosen view is remembered) and an
  auto-generated detail page per run.
- Per-run **analysis** metadata: domain (frequency / time / time-frequency),
  start / end / sampling frequency, and observation time.
- **Source-specific** metadata per type: number found, waveform model (linked),
  frequency coverage, prior link, and number of posterior files; the `NOISE`
  entry shows its noise model.
- A `version` field plus a **Version** column (the run number indicates which
  sources are included; the version is that run's iteration counter).
- `from_metadata` converter that drafts a run's `meta.yaml` from its emitted
  `global_metadata.json` and the sibling per-source metadata files.
- GitHub Pages deployment via GitHub Actions.

### Changed
- The run date now reflects when the run was performed (the submission
  timestamp), not the simulated LISA observation epoch.
- Posterior counts use unique files (duplicated entries are collapsed).

### Removed
- Per-run code-version display and the install run→version table.
- The "Adding a run" page.
