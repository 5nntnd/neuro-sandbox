# Hypothesis and analysis choices (written before any Week 3 classifier results)

Written 2026-10-04. Edit this file only before running the confirmatory analysis, and note any change with its date and reason. These are proposed defaults; change them now if you disagree, not after seeing results.

## Question

Can imagined left-fist vs right-fist movement be classified from scalp EEG above chance, with honest cross-validation, on PhysioNet EEGMMIDB?

The imagined-vowel question (A vs I) is a stretch goal and is out of scope here. It needs its own hypothesis once a dataset with those prompts is chosen.

## Hypothesis

Imagined left vs right fist produces opposite-side mu/beta (8-30 Hz) desynchronization over motor cortex (C3 vs C4), so a CSP + LDA classifier beats chance for some subjects.

## Exploratory vs confirmatory subjects

- **Exploratory: subjects 1-10.** Week 0 already scored them, so their numbers are not clean evidence. Use them to build and debug the pipeline.
- **Confirmatory: subjects 11-20.** Not looked at yet. Run the final pipeline on them once, with the choices below frozen.

## Fixed choices (do not tune on test results)

- Runs 4, 8, 12 (imagined left vs right fist); trials labelled T1 (left) and T2 (right).
- Band-pass 8-30 Hz; epoch window 0.5-3.5 s after cue; no baseline correction.
- CSP with 4 components and `reg='ledoit_wolf'` (closed-form covariance shrinkage, no tuned hyperparameter, chosen because 64 channels with about 15 trials per class per training fold gives a noisy covariance), then LDA, with CSP fitted inside each training fold. Decided 2026-10-04, before any confirmatory run.
- Drop persistently noisy channels with a fixed, label-blind rule, before re-referencing: on the whole continuous recording in its native reference, take each channel's log10 mean power in 30-55 Hz, convert to a robust z-score across that subject's channels (z = (x - median) / (1.4826 * MAD)), and drop channels with z above 3.5 (`experiments/week1_bad_channels.py`). The cutoff is the conventional robust-z limit and is not to be tuned. Same rule for every subject, including the confirmatory set; no hand-picked channels, no interpolation. Report the dropped channels per subject with every result. On subjects 1-10 it dropped 0 to 4 channels each, none over motor cortex (for example only T7 in subject 2). As a robustness check only, never the primary result, also report accuracy with the flagged channels kept. Decided 2026-10-04, from the exploratory subjects and without using labels.
- Re-reference to the common average after dropping those channels and before filtering. The original reference is undocumented (see `datasets.md`). Decided 2026-10-04.
- No ICA in the classifier pipeline; ICA is used only as a diagnostic for eye components. The 8-30 Hz band-pass already removes most blink energy, and per-subject component removal would add a data-dependent choice. Decided 2026-10-04.
- No epoch rejection: all 45 trials per subject are kept. A fixed peak-to-peak threshold on Fp1/Fp2 would discard most trials in several exploratory subjects (for example, over 150 uV in 40 of 45 trials for subject 3 and all 45 for subject 9; `results/week1_eye_events.txt`), and too few trials would be left. Decided 2026-10-04, from the exploratory subjects only.
- Cross-validation: leave-one-run-out (train on two runs, test on the third).
- Metrics per subject: accuracy, 95% confidence interval, Cohen's kappa, permutation p-value (1000 permutations).
- All subjects in the set are reported. No dropping subjects after seeing results.

## What counts as "detected"

- **Per subject:** accuracy at or above about 64% and permutation p < 0.05. Week 0 found this threshold at 45 trials.
- **Group (the claim that matters):** at least 3 of the 10 confirmatory subjects pass the per-subject rule. By chance alone with 10 subjects at alpha = 0.05, 3 or more passing has probability of about 1%, while 2 or more is about 9%, so 2 is not enough.
- **Artifact check:** the CSP patterns and the channels driving the classifier must sit over motor areas. If they sit frontal or temporal (eyes, jaw), the result does not count as brain-based.
- **Eye-event balance check:** report, for the confirmatory subjects, the same left vs right count of epochs with Fp1/Fp2 swings over 150 uV as `experiments/week1_eye_events.py` gives for subjects 1-10 (there the pooled counts were balanced, Fisher p = 0.64). If the pooled counts are lopsided (Fisher p < 0.05), state it as a caveat on any positive result.

## What counts as "not detected"

- Fewer than 3 of 10 confirmatory subjects pass. Report it as a null result with the per-subject table; do not retune the pipeline and rerun on the same subjects.

## Known limits

- 45 trials per subject gives about ±15 points of uncertainty, so single-subject results stay weak evidence.
- Week 0 on subjects 1-10: 2 of 10 beat chance under run-wise CV, so the confirmatory set may well come out null.
