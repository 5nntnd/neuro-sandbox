# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

neuro-sandbox is a personal learning project: decoding mental states from public EEG datasets with Python (MNE, scikit-learn). The plan is in `reference/eeg-learning-plan.md` and the known pitfalls are in `reference/blindspots.md`.

`LOG.md` is a one-sentence-per-entry log of what has been tested and verified, with links to the script and its output.

Code so far: `experiments/week0_noise_check.py` (the Week 0 task in the plan). Setup is a virtual environment plus `pip install -r requirements.txt`. There is no build, lint or test configuration yet.

Update this file once more code, dependencies, and structure are added to the project.

## Repository rules (this repo is public)

- Datasets, downloads and scratch outputs go only in gitignored directories (`data/`, `mne_data/`, `outputs/`). If a new location is needed, add it to `.gitignore` first. Never commit raw or derived data files. `results/` is the exception: it holds the small, curated outputs (text tables, figures) that `LOG.md` links to, and is committed.
- Check a dataset's license (redistribution and citation terms) before committing anything derived from it, including excerpts, processed files and shared figures. Record the license in `reference/datasets.md`.
- Strip notebook outputs before committing (for example with `nbstripout`). Commit notebooks without outputs.
- Before every commit, run `git status` and confirm no data, generated outputs or notebook outputs are staged.
- Follow `reference/blindspots.md` for methodology: use run-, session- or subject-wise cross-validation, fit data-dependent steps inside the CV pipeline, and report confidence intervals and a permutation test rather than a bare accuracy.
- After running a test or experiment, add one sentence to `LOG.md` (status `verified`, `refuted` or `open`, with links to the script and its output) and commit the linked output files under `results/`.
