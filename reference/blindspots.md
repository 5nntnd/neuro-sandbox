# Blindspot pass: neuro-sandbox

Companion to `eeg-learning-plan.md`. A blindspot pass lists what the plan assumes, skips or could get subtly wrong, so the unknown unknowns become known before they cost time. Written 2026-10-04 from a reading of the plan, not from running anything.

Items marked **(verify)** come from memory and have not been checked against a source.

## A. Things that could quietly invalidate results (highest priority)

1. **"Split by session" is impossible on PhysioNet.** Each subject has one session, so trials are correlated in time and plain k-fold leaks drift into the test folds. Use run-wise CV (train on two runs, test on the third) or leave-one-subject-out. BCI Competition IV 2a has two sessions, so it supports a real session split.
2. **Very few trials.** Runs 4, 8 and 12 for one subject give roughly 45 left/right trials, so accuracy has an uncertainty of about ±15 points. About 62-65% is needed to beat chance at p<0.05. Report a confidence interval and a permutation test, never a bare accuracy. (Week 0 shows this visually.)
3. **Muscle and eye artifacts can fake a result.** Subvocalization, jaw and tongue EMG and eye movements correlate with what you imagine, and a classifier can learn those instead of brain activity. This matters most for imagined speech. Use ICA, re-referencing and a notch filter (50/60 Hz), and check what channels and frequencies the model actually uses.
4. **Forking paths.** Time window, filter band, CSP component count and subject selection are all choices. Tuning them on the data you report inflates accuracy, and so does reporting only the best subject. Fix the choices up front or use nested CV.
5. **Block-design confounds.** If each mental state was recorded in its own block, slow drift can separate the classes with no task-related brain signal. Published criticism of this exists for EEG classification **(verify)**. Distrust impressive numbers from block-design datasets.

## B. Science gaps

- **Why 8-30 Hz:** the signal is mu/beta event-related desynchronization over motor cortex, strongest on the side opposite the imagined hand. It explains why accuracy varies between subjects.
- **"BCI illiteracy":** a sizeable minority of people (commonly quoted as 15-30%) produce no usable motor-imagery signal **(verify)**. Near-chance subjects are normal.
- **Scalp EEG is blurry:** volume conduction smears signals, and vowel-related activity is small and anatomically close together. Much informative speech activity (high gamma) is easier to read from implanted electrodes than from the scalp.
- **A vs I may not exist in public data.** As recalled, Kara One uses prompts such as /iy/ and /uw/ plus syllables and words **(verify)**. Redefine the vowel question to match what the dataset offers before building on it.
- **Imagery type matters:** kinesthetic imagery (feeling the movement) tends to work better than visual imagery. Public datasets don't always say which was used.

## C. Machine-learning pitfalls

- **EEGNet on ~45 trials will overfit.** BCI IV 2a (about 288 trials per subject) or pooled subjects give a deep net something to learn from.
- **Accuracy alone is thin.** Add Cohen's kappa and a chance-level test.
- **Data leakage:** fit anything data-dependent (CSP, scalers, feature selection) inside the CV pipeline, as the starter code does for CSP.
- **Reproducibility:** pin library versions, set random seeds, record the dataset version.

## D. Practical and repo-specific

- **The repo is public.** Don't commit data. Datasets are large and some licenses forbid redistribution. Keep data in gitignored directories (`data/`, `outputs/`) and strip notebook outputs before committing. See `CLAUDE.md`.
- **Licenses:** check each dataset's citation and use terms before committing anything derived from it.
- **Disk and downloads:** MOABB and OpenNeuro downloads can reach many GB.
- **Assumed prerequisites:** filtering and sampling basics, epoching and baselines, what CSP does (covariance and eigenvectors) and kinds of CV. Four evenings is optimistic if these are new.
- **Starter code was untested** when the plan was written. `experiments/week0_noise_check.py` is the tested version.

## E. Found by running Week 0 and Week 1 (2026-10-04)

These were verified on subjects 1-10; the evidence is in `LOG.md`.

- **T1/T2 change meaning between runs.** In runs 4, 8, 12 they are left/right fist imagery; in runs 6, 10, 14 they are both fists/both feet, and runs 3, 7, 11 are real movement. The PhysioNet page does not give the run table (MNE's documentation does). The scripts assert the runs; see `datasets.md`.
- **The recording reference is undocumented.** Not in the PhysioNet pages, the BCI2000 wiki or Schalk 2004. Do not trust "mastoid" from secondary metadata. We re-reference to the common average ourselves.
- **Eye artifacts leak into motor channels** by volume conduction at about half their frontal size, so a clean-looking C3/C4 trace can still carry blink energy (section A3 confirmed by eye).
- **Large frontal swings are everywhere.** Over 150 uV on Fp1/Fp2 in most trials of several subjects, so fixed-threshold epoch rejection would throw most data away. They are balanced between left and right trials, which is what matters.
- **Mains noise and muscle vary by subject.** 60 Hz from +2 to +42 dB; high 30-55 Hz power at the edges in subjects 5, 7 and 9.
- **One bad channel can spread through the average reference.** Subject 2's T7 is noisy throughout (possibly an electrode or hardware contact problem; the dataset documents nothing). A fixed label-blind rule handles it; see `hypothesis.md`.
- **Tooling gotchas.** MNE shows the Nyquist frequency (80 Hz) as the "low-pass" of these files, which have no hardware filters at all, and concatenating runs adds boundary annotations that code must skip.

## F. Gaps in the goal itself

- **No hypothesis or stopping rule.** Decide in advance what counts as "detected" and what counts as "not detected". A null result on imagined vowels is valid and likely.
- **Terminology:** "imagined speech", "inner speech" and "silent articulation" are different tasks, and papers mix them.
- **Reading list (verify exact titles):** Lotte et al. (2018), a review of EEG classification algorithms for BCI; the MOABB paper by Jayaram and Barachant; the EEGNet paper by Lawhern et al.
