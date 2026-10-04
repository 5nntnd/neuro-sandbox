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
- CSP with 4 components, then LDA, with CSP fitted inside each training fold.
- Cross-validation: leave-one-run-out (train on two runs, test on the third).
- Metrics per subject: accuracy, 95% confidence interval, Cohen's kappa, permutation p-value (1000 permutations).
- All subjects in the set are reported. No dropping subjects after seeing results.

## What counts as "detected"

- **Per subject:** accuracy at or above about 64% and permutation p < 0.05. Week 0 found this threshold at 45 trials.
- **Group (the claim that matters):** at least 3 of the 10 confirmatory subjects pass the per-subject rule. By chance alone with 10 subjects at alpha = 0.05, 3 or more passing has probability of about 1%, while 2 or more is about 9%, so 2 is not enough.
- **Artifact check:** the CSP patterns and the channels driving the classifier must sit over motor areas. If they sit frontal or temporal (eyes, jaw), the result does not count as brain-based.

## What counts as "not detected"

- Fewer than 3 of 10 confirmatory subjects pass. Report it as a null result with the per-subject table; do not retune the pipeline and rerun on the same subjects.

## Known limits

- 45 trials per subject gives about ±15 points of uncertainty, so single-subject results stay weak evidence.
- Week 0 on subjects 1-10: 2 of 10 beat chance under run-wise CV, so the confirmatory set may well come out null.
