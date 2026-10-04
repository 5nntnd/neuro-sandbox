# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

neuro-sandbox is a personal learning project: decoding mental states from public EEG datasets with Python (MNE, scikit-learn). The plan is in `reference/eeg-learning-plan.md` and the known pitfalls are in `reference/blindspots.md`.

`LOG.md` is a one-sentence-per-entry log of what has been tested and verified, with links to the script and its output.

`reference/hypothesis.md` holds the frozen analysis choices and the "detected / not detected" rules, `reference/datasets.md` the dataset license, run table and recording notes, and `reference/week1-summary.md` what Week 1 found.

Code so far, all in `experiments/` (run from the repo root with the virtual environment active; setup is `python -m venv .venv`, activate it, `pip install -r requirements.txt`):

- `week0_noise_check.py`: Week 0 accuracy-noise demonstration.
- `week1_inspect_raw.py`: one-subject look at sampling, events, line noise and ICA. Its `load_raw`, `line_noise_report` and `RESULTS_DIR` are imported by the other Week 1 scripts, and importing it sets the non-interactive matplotlib backend.
- `week1_survey.py`, `week1_eye_events.py`, `week1_bad_channels.py`: per-subject data-quality checks on subjects 1-10, each writing a table to `results/`.
- `week1_browse_raw.py` (trace browser with a channel checklist and notes) and `week1_topomap_player.py` (scalp map with a time slider): interactive tools. They do not import the non-interactive backend. `browse_raw.bat` and `topomap_player.bat` in the repo root start them with a double-click.

All of these use runs 4, 8, 12 only (T1 = left, T2 = right; they assert this) and refuse subjects above 10 unless `--allow-confirmatory` is passed. There is no build, lint or test configuration yet. Update this file when the structure changes.

## Repository rules (this repo is public)

- Datasets, downloads and scratch outputs go only in gitignored directories (`data/`, `mne_data/`, `outputs/`). If a new location is needed, add it to `.gitignore` first. Never commit raw or derived data files. `results/` is the exception: it holds the small, curated outputs (text tables, figures) that `LOG.md` links to, and is committed.
- Check a dataset's license (redistribution and citation terms) before committing anything derived from it, including excerpts, processed files and shared figures. Record the license in `reference/datasets.md`.
- Strip notebook outputs before committing (for example with `nbstripout`). Commit notebooks without outputs.
- Before every commit, run `git status` and confirm no data, generated outputs or notebook outputs are staged.
- Follow `reference/blindspots.md` for methodology: use run-, session- or subject-wise cross-validation, fit data-dependent steps inside the CV pipeline, and report confidence intervals and a permutation test rather than a bare accuracy.
- Subjects 1-10 are exploratory; subjects 11-20 are the confirmatory set and must not be run through a classifier or used to tune any choice until the frozen pipeline in `reference/hypothesis.md` is final. Change a frozen choice only before that run, and record the date and reason in `hypothesis.md`.
- `results/` is for curated, linked evidence and `outputs/` is gitignored scratch (for example the browser's `week1_notes_s<N>.csv`). Name result files `week<N>_<what>_s<subject>.<ext>` where they are per subject.
- After running a test or experiment, add one sentence to `LOG.md` (status `verified`, `refuted` or `open`, with links to the script and its output) and commit the linked output files under `results/`.
