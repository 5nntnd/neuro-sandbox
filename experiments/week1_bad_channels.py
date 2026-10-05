"""Week 1: find persistently noisy channels with a fixed, label-blind rule.

Run (from the repo root, with the virtual environment active):
    python experiments/week1_bad_channels.py [--subjects 10]

Rule (computed on the whole continuous recording, before re-referencing, never using the
left/right labels or any classifier output): for each channel take the log10 mean power in
30-55 Hz, convert to a robust z-score across that subject's channels
(z = (x - median) / (1.4826 * MAD)), and flag channels with z above THRESHOLD. The cutoff
3.5 is the conventional robust-z outlier limit, not tuned on this data.

Subjects above 10 are the confirmatory set (see reference/hypothesis.md) and are refused
unless --allow-confirmatory is passed.
"""
import argparse
import sys
from pathlib import Path

import mne
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import RESULTS_DIR, load_raw  # noqa: E402

BAND = (30, 55)
THRESHOLD = 3.5
N_EXPLORATORY = 10

mne.set_log_level("ERROR")


def robust_z_from_raw(raw):
    """Channel names and robust z of 30-55 Hz power; raw must be in its native reference."""
    psd = raw.compute_psd(fmin=BAND[0], fmax=BAND[1], picks="eeg")
    log_power = np.log10(psd.get_data().mean(axis=1))
    med = np.median(log_power)
    mad = np.median(np.abs(log_power - med))
    return raw.ch_names, (log_power - med) / (1.4826 * mad)


def robust_z(subject):
    return robust_z_from_raw(load_raw(subject))  # native reference, no re-referencing yet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="survey subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)

    lines = ["subject\tn_flagged\tflagged channels (robust z)"]
    for s in range(1, args.subjects + 1):
        print(f"subject {s}...", flush=True)
        names, z = robust_z(s)
        order = np.argsort(z)[::-1]
        flagged = [f"{names[i]} ({z[i]:.1f})" for i in order if z[i] > THRESHOLD]
        lines.append(f"{s}\t{len(flagged)}\t{', '.join(flagged) if flagged else '-'}")
        if s == 2:
            lines.append(f"  (subject 2, T7 robust z = {z[names.index('T7')]:.1f})")
    lines += [
        "",
        f"mne {mne.__version__}; whole recording, native reference; log10 mean power {BAND[0]}-{BAND[1]} Hz per channel; "
        f"flagged when robust z > {THRESHOLD}.",
    ]
    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week1_bad_channels.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
