# Lab log

What has been tested, and what came out. One sentence per entry, newest first. Status is `verified`, `refuted` or `open`; each entry links the script and its committed output in `results/`.

## 2026-10-04

- `open` Shuffled 5-fold does not consistently score higher than run-wise CV (subject 1: 0.75 vs 0.62, subject 9: 0.36 vs 0.53), so the leakage concern is not confirmed on this sample. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Subject 1's 62% is not significant (permutation p = 0.065), and shuffled labels alone score anywhere from about 0.30 to 0.70 on 45 trials. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Only subjects 2 and 7 of 10 beat chance with leave-one-run-out CV (64% needed at 45 trials). [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Every subject has 45 left/right trials, so each 95% confidence interval spans about ±15 points. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt)
- `verified` The Week 0 script runs end to end on subjects 1-10 and a rerun gives identical numbers. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt)
