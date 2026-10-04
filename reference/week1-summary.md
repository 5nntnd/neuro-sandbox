# Week 1 summary: what the raw data looks like

Written 2026-10-04 from subjects 1-10 (exploratory set only). Evidence is in `LOG.md`; each line below points to the entry or file behind it.

## The data

- PhysioNet EEGMMIDB, runs 4, 8, 12 (imagined left vs right fist), 64 channels at 160 Hz, about 6 minutes per subject.
- Every subject has 45 task trials (21-24 per class). Every cue lasts at least 4.1 s, so the frozen 0.5-3.5 s epoch window always fits.
- Reference and ground electrodes are not documented anywhere we could find (`datasets.md`). The EDF headers list no hardware filters.
- T1/T2 mean left/right only in runs 4, 8, 12; the scripts assert this.

## What we found

- **Mains noise (60 Hz)** varies a lot between subjects, from +2 to +42 dB (strongest in 5 and 7). It sits outside the 8-30 Hz band.
- **Blinks** are paired spikes about 0.3 s wide, biggest on Fp1/Fp2. Seen by eye in subjects 2, 5 and 9 (clear in 2 and 5; subject 9's frontal channels are swamped by fast noise). ICA finds one or more eye components in every subject (diagnostic only).
- **Eye artifacts leak into motor channels** by volume conduction at about half the size (subject 2, 99-102 s).
- **Muscle (30-55 Hz)** power is high at the edges in subjects 5 and 9 (and overall in 7). Left vs right trials do not differ on it (0-2 of 64 channels per subject, about 3 expected by chance).
- **Large frontal swings** (over 150 uV on Fp1/Fp2) are evenly split between left and right trials (pooled Fisher p = 0.64), so eyes alone are unlikely to produce a left/right result. They are frequent, though: most trials in subjects 1, 3, 6, 9, 10 exceed the threshold.
- **Persistently noisy channels** exist: subject 2's T7 is noisy throughout (its 30-55 Hz power is 7.5 robust z-scores above the other channels). A fixed rule flags 0 to 4 channels per subject, mostly frontal and temporal edge channels and never motor ones. The cause is not documented; a poor electrode contact or hardware fault is plausible but unverified.

## Decisions made (all in `hypothesis.md`)

Drop persistently noisy channels with a fixed label-blind rule (robust z above 3.5 in 30-55 Hz power) and report them per subject; common average reference afterwards; no ICA in the pipeline; no epoch rejection; CSP 4 components with Ledoit-Wolf shrinkage; leave-one-run-out CV; subjects 11-20 held back as the confirmatory set; the "detected" rule (at least 3 of 10 confirmatory subjects, each at about 64% and permutation p < 0.05); and a report of the eye-event balance for the confirmatory subjects.

## Still open

- **Structural check of subjects 11-20** (files present, 160 Hz, 64 channels, 45 trials, cue lengths) without looking at any classifier output.
- Only 3 subjects were paged through by eye, so the artifact picture is a sample, not a census.

## Next

Week 2: epoch with the frozen settings and plot C3/C4 mu/beta band power for left vs right imagery on subjects 1-10. No classifier yet.
