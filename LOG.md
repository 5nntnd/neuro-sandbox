# Lab log

What has been tested, and what came out. One sentence per entry, newest first. Status is `verified`, `refuted` or `open`; each entry links the script and its committed output in `results/`.

## 2026-10-04

- `verified` Subject 2 has only weak 60 Hz noise (+2.1 dB, vs +11 dB for subject 1) and one frontal eye component (ICA000), so mains noise varies between subjects. [script](experiments/week1_inspect_raw.py) · [output](results/week1_inspect_raw_s2.txt) · [figure](results/week1_psd_s2.png)
- `verified` ICA (20 components) on subject 1 finds one frontal eye-blink component (ICA000, flagged by Fp1/Fp2 correlation), and blinks are visible as large frontal spikes in the raw traces. [script](experiments/week1_inspect_raw.py) · [output](results/week1_inspect_raw_s1.txt) · [figure](results/week1_ica_components_s1.png) · [traces](results/week1_traces_s1.png)
- `verified` Subject 1 has 60 Hz mains noise (+11 dB over neighbouring frequencies) and no visible 50 Hz peak, at 160 Hz sampling (EDF headers list no hardware high-pass, low-pass or notch), so a 60 Hz software notch would be the right one if ever needed. [script](experiments/week1_inspect_raw.py) · [output](results/week1_inspect_raw_s1.txt) · [figure](results/week1_psd_s1.png)
- `open` Shuffled 5-fold does not consistently score higher than run-wise CV (subject 1: 0.75 vs 0.62, subject 9: 0.36 vs 0.53), so the leakage concern is not confirmed on this sample. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Subject 1's 62% is not significant (permutation p = 0.065), and shuffled labels alone score anywhere from about 0.30 to 0.70 on 45 trials. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Only subjects 2 and 7 of 10 beat chance with leave-one-run-out CV (64% needed at 45 trials). [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt) · [figure](results/week0_noise_check.png)
- `verified` Every subject has 45 left/right trials, so each 95% confidence interval spans about ±15 points. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt)
- `verified` The Week 0 script runs end to end on subjects 1-10 and a rerun gives identical numbers. [script](experiments/week0_noise_check.py) · [output](results/week0_noise_check.txt)
