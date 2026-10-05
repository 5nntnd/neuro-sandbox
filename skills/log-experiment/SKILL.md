---
name: log-experiment
description: Use after running a test or experiment in this repo. Adds the one-sentence LOG.md entry, checks outputs are in results/, and proposes a commit without committing.
---

 # Log an experiment

      Follow these steps in order after a script has run and its output exists.

      1. **Check the output.** Confirm the script's text/figure outputs are in `results/` and named
         `week<N>_<what>_s<subject>.<ext>` where they are per subject. Scratch files belong in
         the gitignored `outputs/`, not `results/`.
      2. **Write one LOG.md sentence.** Add it at the top of the newest date section (create the
         date heading if needed). Format:
         `- \`verified|refuted|open\` <one sentence stating the result, including how weak it is> [script](experiments/...) · [output](results/...)`
         Say plainly when the result is weak, mixed or not what was expected. Use `open` if the
         question is not settled.
      3. **Respect the frozen plan.** If the run touched subjects above 10 or changed a choice in
         `reference/hypothesis.md`, stop and tell the user instead of logging it.