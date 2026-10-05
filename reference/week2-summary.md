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
- **Could subjects 1, 3 and 6 be left-handed?** Judged not likely (2026-10-05), but not verified. Cannot be settled from what we have. The PhysioNet page and the papers we checked give no handedness for any subject (checked 2026-10-05, `datasets.md`; the OpenNeuro copy's participant table is unchecked), and nothing in our data tells us. Their right-minus-left maps show a roughly uniform offset over the whole scalp (subject 1 mostly lower for right imagery, subject 3 mostly higher), not a mirrored left-right pair over the motor strip, which is what handedness would more plausibly give. A uniform offset points to the person's state (drowsiness, attention drifting between runs), electrode contact, or left and right trials being unevenly spread over the three runs. The lateralization index subtracts a uniform offset, so those subjects just have little left-right signal left. Cap placement or rotation cannot be ruled out (no data on it) but nothing in the maps points to it.

## Were channels mixed up? (checked 2026-10-05)

`experiments/week2_channel_check.py`, subjects 1-10, descriptive:

- **Neighbour correlation (task-independent).** A channel with the wrong label (really a far electrode) would correlate near zero with its labelled neighbours. In subject 6, C3 is normal (r = 0.78) and C4 is somewhat lower (0.59, subject median 0.71), not near zero. The near-zero channels are edge ones (for example T9), as in other subjects.
- **Best channel pair for the effect.** Over all ordered channel pairs, with a label-permutation p-value that accounts for the search, subject 6 has no pair beyond chance in mu (best AFz to CP5, p = 0.16) or beta (p = 0.36), and its C3-to-C4 pair ranks near the bottom (3324 of 3906 in mu), the wrong direction. So no other channel carries the "correct" behaviour in subject 6.
- **Positive control.** Where the effect is clear (subjects 7, 8 and 10), the best pair sits on or next to C3/C4 (CP3 to C4, C3 to C4, Fz to C4), which supports the labels being right. Other significant best pairs are odd, far-apart pairs (subject 1 beta, PO8 to F8, p = 0.023), about as many as chance gives over 20 tests.
- **Caveat.** This cannot detect a swap between mirror channels such as C3 and C4 themselves, or between neighbours, because their signals look alike. A C3/C4 swap would show as a reversed effect in every subject, but subjects 7, 8 and 10 show the predicted direction, so a global swap is ruled out.

## Still open

- Structural check of subjects 11-20, still due before the confirmatory run (see `week1-summary.md`).

## Next

Week 3: CSP + LDA with leave-one-run-out CV on subjects 1-10, reusing `preprocess`.
