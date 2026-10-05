# Week 2 summary: is there a left/right mu/beta effect?

Written 2026-10-05 from subjects 1-10 (exploratory set only). Evidence is in `LOG.md`; figures and the table are in `results/week2_*`.

## Glossary: mu and beta

Two frequency bands of brain rhythm over motor areas. Both are strong when the motor cortex is idle and drop (event-related desynchronization, ERD) when you move or imagine moving.

- **Mu, 8-12 Hz.** The slower rhythm over the motor strip.
- **Beta, 13-30 Hz.** The faster rhythm, which also drops during movement and often rebounds afterwards.

Imagining a right-hand movement should lower mu and beta over the left motor cortex (C3), and the reverse for the left hand (C4). That contralateral drop is the signal the project tries to decode. The frozen band-pass (8-30 Hz) covers both.

## What we found

- The frozen preprocessing is one function, `preprocess(subject)` in `experiments/week2_preprocess.py`, giving 45 epochs per subject.
- Lateralization index LI = log10 power at C4 minus C3; effect = mean LI(right) minus mean LI(left), predicted positive.
- **Mu:** 8 of 10 subjects have the predicted sign, but only subjects 7, 8 and 10 have a 95% bootstrap CI wholly above 0, and subject 6 is wholly below 0 (the wrong way). Sign test p = 0.055.
- **Beta:** 7 of 10 have the predicted sign (chance level), 2 (subjects 4 and 7) are clearly above 0 and subject 5 is clearly below 0.
- Median effects are small (+0.087 mu, +0.040 beta, in log10 units).
- Scalp maps of right minus left power show a left-right pair over motor cortex clearly only in subject 7 (and subject 10 in mu). Most other subjects look diffuse, some with strong rim (frontal, temporal) patches; subjects 1, 3 and 6 look like whole-head shifts rather than a left-right pair.
- **When does power change (rest-baseline view, `week2_erd_timecourse.png`)?** Both sides drop together from about 0.3 s after the cue and stay down through the window, with a brief transient right at the cue that the frozen window (starting at 0.5 s) skips. The contralateral side is only slightly below the ipsilateral on average (0.5-3.5 s, contra minus ipsi: -5.3 points in mu, -3.0 in beta) and there is no average lateralization before the cue (+0.3 mu, +3.0 beta). Single subjects swing by 20-40 points before the cue as well, so what looked like early lefting or righting in the trace browser is within the trial-to-trial noise at about 22 trials per hand. Nothing here says the 0.5-3.5 s window is badly placed.
- Reading: a real lateralization for about 3 of 10 subjects in mu and 2 in beta, and nothing distinguishable from noise (or the wrong way) for the rest. Expect Week 3 to work for a few subjects at most.

## Questions raised and where they stand

- **Can a different time window flip subjects from "CI includes 0" to "excludes 0"?** Probably some would, which is the reason not to do it. The rest-baseline plot (below) gave no timing reason to move it. Trying several windows across 10 subjects and 2 bands and keeping the one that looks best is tuning on results (a few subjects cross the line by chance), and choosing it after seeing results would contaminate the confirmatory set. A window change is allowed before the confirmatory run only if it is chosen from the timing of the response (for example the rest-baseline plot), not from which subjects turn significant; it is then recorded with date and reason in `hypothesis.md`. Some subjects seemed to start imagining before the cue in the trace browser; the rest-baseline plot checked that descriptively and found no average pre-cue lateralization. See `hypothesis.md`.
- **Could subjects 1, 3 and 6 be left-handed?** Open and unverified. The dataset metadata was not checked for handedness (`datasets.md`), and nothing in our data tells us. Their maps do not show a swapped left-right pair, which is what handedness would more plausibly give, so other explanations (attention drifting between runs, muscle activity, noisy epochs) are as likely.

## Still open

- Structural check of subjects 11-20, still due before the confirmatory run (see `week1-summary.md`).

## Next

Week 3: CSP + LDA with leave-one-run-out CV on subjects 1-10, reusing `preprocess`.
