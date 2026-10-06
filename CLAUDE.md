# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

neuro-sandbox is a personal learning project: decoding mental states from public EEG datasets with Python (MNE, scikit-learn). The plan is in `reference/eeg-learning-plan.md` and the known pitfalls are in `reference/blindspots.md`.

`LOG.md` is a one-sentence-per-entry log of what has been tested and verified, with links to the script and its output.

`reference/hypothesis.md` holds the frozen analysis choices and the "detected / not detected" rules, `reference/datasets.md` the dataset license, run table and recording notes, `reference/week1-summary.md` what Week 1 found, and `reference/week2-summary.md` what Week 2 found (with a mu/beta glossary and the rule for changing the epoch window).

Code so far, all in `experiments/` (run from the repo root with the virtual environment active; setup is `python -m venv .venv`, activate it, `pip install -r requirements.txt`):

- `week0_noise_check.py`: Week 0 accuracy-noise demonstration.
- `week1_inspect_raw.py`: one-subject look at sampling, events, line noise and ICA. Its `load_raw`, `line_noise_report` and `RESULTS_DIR` are imported by the other Week 1 scripts, and importing it sets the non-interactive matplotlib backend.
- `week1_survey.py`, `week1_eye_events.py`, `week1_bad_channels.py`: per-subject data-quality checks on subjects 1-10, each writing a table to `results/`.
- `week1_browse_raw.py` (trace browser with a channel checklist and notes) and `week1_topomap_player.py` (scalp map with a time slider): interactive tools. They do not import the non-interactive backend. `browse_raw.bat` and `topomap_player.bat` in the repo root start them with a double-click.

- `week2_preprocess.py`: `preprocess(subject)` returns the 45 frozen-pipeline epochs and the dropped channels (also refuses subjects above 10 unless `allow_confirmatory=True`). `week2_band_power.py`: mu/beta power at C3/C4, left vs right, subjects 1-10, writing `results/week2_band_power.txt` and three figures (C3/C4 lines, per-subject effect with CI, scalp maps). `week2_erd_timecourse.py`: descriptive mu/beta power over time relative to rest (contralateral vs ipsilateral), using a wider epoch only for the plot. `week2_channel_check.py`: neighbour-correlation and best-channel-pair checks for mislabelled channels.

- `week3_csp_lda.py`: CSP (4 components, Ledoit-Wolf) + LDA, leave-one-run-out, subjects 1-10 only; per-subject accuracy, CI, kappa, permutation p (1000), dropped channels, a flagged-channels-kept robustness column and a pattern/region artifact check, writing `results/week3_csp_lda.txt` and two figures. Run index is derived from the event sample (each run is 20000 samples).

- `week3_movement_control.py`: positive control, the same frozen pipeline on real-movement runs 3, 7, 11 (subjects 1-10 only; diagnostic, see `hypothesis.md`). `load_raw` and `preprocess` take an optional `runs` argument for it; the default is unchanged.

All of these use runs 4, 8, 12 only (except the movement control, which uses runs 3, 7, 11) (T1 = left, T2 = right; they assert this) and refuse subjects above 10 unless `--allow-confirmatory` is passed. There is no build, lint or test configuration yet. Update this file when the structure changes.

## Where we are (update at the end of each week)

Weeks 0, 1 and 2 are done (last updated 2026-10-05). At the start of a session read, in this order: `reference/week2-summary.md` (what Week 2 found, mu/beta glossary, rule for changing the epoch window, the channel mix-up check), `reference/hypothesis.md` (frozen choices), the Week 3 section of `reference/eeg-learning-plan.md`, and the top of `LOG.md`. Then say what you understood and propose the Week 3 plan before writing code.

**Week 2 result:** with the frozen preprocessing, mu lateralization (C4 minus C3, right minus left imagery) has the predicted sign in 8 of 10 exploratory subjects and beta in 7 of 10, but it is inconsistent between subjects (clear in subjects 7, 8, 10 in mu; subject 6 clearly the wrong way) and the effects are small. Both hemispheres drop together from about 0.3 s after the cue; the frozen 0.5-3.5 s window stays. No sign of mislabelled channels. Handedness is undocumented for the dataset and judged not likely to matter (not verified). Expect Week 3 to work for a few subjects at most, and a null result on the confirmatory set is realistic.

**Next: Week 3**, on subjects 1-10 only: CSP (4 components, `reg='ledoit_wolf'`) + LDA, leave-one-run-out CV with CSP fitted inside each training fold, reusing `preprocess(subject)` from `experiments/week2_preprocess.py`. Report per subject: accuracy, 95% CI, Cohen's kappa, permutation p (1000), and the dropped channels; also run once with the flagged channels kept (`drop_flagged=False`) as a robustness check only. Check which channels and patterns drive the classifier (motor, not frontal or temporal). If CSP does poorly in a way that looks like noise, a surface Laplacian is the first thing to consider, decided on principle (not by which subjects improve) and recorded with date and reason in `hypothesis.md`. Do not run subjects 11-20 through any classifier.

Still open: the structural check of subjects 11-20 (files, 160 Hz, 64 channels, 45 trials, cue lengths; no classifier output), due before the confirmatory run, and the OpenNeuro copy's participant table (ds004362) is the only unchecked source for handedness. `agents/experiment-logger.md` and `skills/log-experiment/SKILL.md` sit at the repo root (a LOG.md helper agent and skill); they are not auto-loaded from there.

Working habits that have held so far: propose a commit message and wait for the user's go-ahead before committing, then again before pushing; stage files by name and show `git status` first; leave the user's untracked files out unless told; add a `LOG.md` entry for each test and commit its output under `results/`; say plainly when a result is weak or a screenshot does not show what was claimed. Data for subjects 1-10 is already downloaded in the gitignored `data/` folder; on a fresh clone the scripts download it again. The shell is PowerShell on Windows: run scripts with `.venv\Scripts\python experiments\<script>.py`.

## Repository rules (this repo is public)

- Datasets, downloads and scratch outputs go only in gitignored directories (`data/`, `mne_data/`, `outputs/`). If a new location is needed, add it to `.gitignore` first. Never commit raw or derived data files. `results/` is the exception: it holds the small, curated outputs (text tables, figures) that `LOG.md` links to, and is committed.
- Check a dataset's license (redistribution and citation terms) before committing anything derived from it, including excerpts, processed files and shared figures. Record the license in `reference/datasets.md`.
- Strip notebook outputs before committing (for example with `nbstripout`). Commit notebooks without outputs.
- Before every commit, run `git status` and confirm no data, generated outputs or notebook outputs are staged.
- Follow `reference/blindspots.md` for methodology: use run-, session- or subject-wise cross-validation, fit data-dependent steps inside the CV pipeline, and report confidence intervals and a permutation test rather than a bare accuracy.
- Subjects 1-10 are exploratory; subjects 11-20 are the confirmatory set and must not be run through a classifier or used to tune any choice until the frozen pipeline in `reference/hypothesis.md` is final. Change a frozen choice only before that run, and record the date and reason in `hypothesis.md`.
- `results/` is for curated, linked evidence and `outputs/` is gitignored scratch (for example the browser's `week1_notes_s<N>.csv`). Name result files `week<N>_<what>_s<subject>.<ext>` where they are per subject.
- After running a test or experiment, add one sentence to `LOG.md` (status `verified`, `refuted` or `open`, with links to the script and its output) and commit the linked output files under `results/`.
