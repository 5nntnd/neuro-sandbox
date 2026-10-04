"""Week 1: do large eye artifacts fall more often in left or right trials?

Run (from the repo root, with the virtual environment active):
    python experiments/week1_eye_events.py [--subjects 10]

For each subject, counts epochs (frozen 0.5-3.5 s window after the cue) whose peak-to-peak
swing on Fp1 or Fp2 exceeds a threshold, separately for left and right trials, and tests
whether the counts differ (Fisher exact test). If eye events were spread evenly across the
two classes they cannot explain a left/right result; a lopsided count would be a warning.
Data is average-referenced and band-passed 1-40 Hz, which keeps blinks visible. This is a
diagnostic only; no classifier is run.

Subjects above 10 are the confirmatory set (see reference/hypothesis.md) and are refused
unless --allow-confirmatory is passed.
"""
import argparse
import sys
from pathlib import Path

import mne
import numpy as np
from scipy.stats import fisher_exact

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import RESULTS_DIR, load_raw  # noqa: E402

TMIN, TMAX = 0.5, 3.5  # frozen epoch window, see reference/hypothesis.md
THRESHOLDS_UV = [100, 150, 200]
EYE_CHANNELS = ["Fp1", "Fp2"]
N_EXPLORATORY = 10

mne.set_log_level("ERROR")


def eye_counts(subject):
    raw = load_raw(subject)
    raw.set_eeg_reference("average", projection=False)  # frozen pipeline choice
    raw.filter(1, 40)
    events, _ = mne.events_from_annotations(raw, event_id=dict(T1=2, T2=3))
    epochs = mne.Epochs(raw, events, dict(left=2, right=3), tmin=TMIN, tmax=TMAX,
                        baseline=None, preload=True)
    data = epochs.get_data(picks=EYE_CHANNELS) * 1e6  # trials x channels x times, microvolts
    p2p = (data.max(axis=2) - data.min(axis=2)).max(axis=1)  # worst of Fp1/Fp2 per trial
    labels = epochs.events[:, 2]
    rows = {}
    for thr in THRESHOLDS_UV:
        hit = p2p > thr
        left, right = int(hit[labels == 2].sum()), int(hit[labels == 3].sum())
        n_left, n_right = int((labels == 2).sum()), int((labels == 3).sum())
        p = fisher_exact([[left, n_left - left], [right, n_right - right]])[1]
        rows[thr] = (left, n_left, right, n_right, p)
    return rows, float(np.median(p2p))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="survey subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)

    header = ["subject", "median_p2p_uV"] + [f"{t}uV_left/right(p)" for t in THRESHOLDS_UV]
    lines = ["\t".join(header)]
    totals = {t: [0, 0, 0, 0] for t in THRESHOLDS_UV}
    for s in range(1, args.subjects + 1):
        print(f"subject {s}...", flush=True)
        rows, med = eye_counts(s)
        cells = [str(s), f"{med:.0f}"]
        for t in THRESHOLDS_UV:
            left, n_left, right, n_right, p = rows[t]
            cells.append(f"{left}/{n_left} vs {right}/{n_right} (p={p:.2f})")
            for i, v in enumerate((left, n_left, right, n_right)):
                totals[t][i] += v
        lines.append("\t".join(cells))
    lines.append("")
    for t in THRESHOLDS_UV:
        left, n_left, right, n_right = totals[t]
        p = fisher_exact([[left, n_left - left], [right, n_right - right]])[1]
        lines.append(f"All subjects pooled, >{t} uV: left {left}/{n_left}, right {right}/{n_right} (Fisher p={p:.2f})")
    lines += [
        "",
        f"mne {mne.__version__}; average reference; 1-40 Hz; epochs {TMIN}-{TMAX} s; "
        f"peak-to-peak on the larger of {EYE_CHANNELS[0]} and {EYE_CHANNELS[1]}.",
        "Cells are: trials over threshold / trials, left vs right. Per-subject p-values are not "
        "corrected for the 10 subjects x 3 thresholds; read them as a diagnostic, not a test result.",
    ]
    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week1_eye_events.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
