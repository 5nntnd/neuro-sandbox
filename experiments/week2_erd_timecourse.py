"""Week 2 (descriptive): mu/beta power over time relative to rest, contralateral vs ipsilateral to the imagined hand.

Run (from the repo root, with the virtual environment active):
    python experiments/week2_erd_timecourse.py

Purpose: see WHEN power changes relative to the cue (does lateralization start before the cue, or
late?) without touching the frozen 0.5-3.5 s classification window. Nothing here selects a window by
subject-level significance; the numbers are descriptive.

Method: the frozen preprocessing with a wider epoch (-2.5 to 4.0 s around the cue; the rest period
before a cue lasts about 4.2 s and every cue at least 4.1 s). Morlet wavelet power (n_cycles = f/2) at
C3 and C4, averaged over the band, then over trials within each imagined hand. Per channel and hand:
ERD% = (power - rest) / rest * 100, rest = mean over -2.0 to -1.0 s (fixed in advance, mid-rest).
Contralateral = C4 for left imagery and C3 for right imagery; ipsilateral = the other channel.
Prediction: contralateral falls below ipsilateral after the cue (more negative ERD%).

Summary table: contra minus ipsi ERD% (percentage points; negative as predicted) in three windows:
-1.0 to 0 s (before the cue), 0 to 0.5 s, and 0.5 to 3.5 s (the frozen window).
"""
import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import RESULTS_DIR  # noqa: E402
from week2_preprocess import N_EXPLORATORY, TMAX, TMIN, preprocess  # noqa: E402

WINDOW = (-2.5, 4.0)
CROP = (-2.0, 3.8)  # drop wavelet edge effects
BASELINE = (-2.0, -1.0)
BANDS = {"mu (8-12 Hz)": (8, 12), "beta (13-30 Hz)": (13, 30)}
CONTRAST_WINDOWS = {"-1.0 to 0 s": (-1.0, 0.0), "0 to 0.5 s": (0.0, 0.5), "0.5 to 3.5 s": (TMIN, TMAX)}
CONTRA, IPSI = "#1c5cab", "#898781"  # blue ramp step 550 and the muted gray: contra is the signal, ipsi the reference
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
FREQS = np.arange(8.0, 31.0, 1.0)


def erd_curves(epochs, band):
    """Return times and ERD% (contra, ipsi) averaged over trials of both hands, plus per-hand ERD%."""
    tfr = epochs.compute_tfr("morlet", freqs=FREQS, n_cycles=FREQS / 2, picks=["C3", "C4"], average=False,
                             output="power", verbose=False)
    tfr.crop(*CROP)
    power = tfr.get_data()  # (epochs, channels [C3, C4], freqs, times)
    sel = (FREQS >= band[0]) & (FREQS <= band[1])
    power = power[:, :, sel, :].mean(axis=2)  # (epochs, channels, times)
    times = tfr.times
    base = (times >= BASELINE[0]) & (times <= BASELINE[1])
    is_right = epochs.events[:, 2] == epochs.event_id["right"]
    out = {}
    for hand, mask in (("left", ~is_right), ("right", is_right)):
        m = power[mask].mean(axis=0)  # (channels, times)
        out[hand] = (m / m[:, base].mean(axis=1, keepdims=True) - 1) * 100
    # channel index: 0 = C3, 1 = C4. Left imagery: contra = C4; right imagery: contra = C3.
    contra = (out["left"][1] + out["right"][0]) / 2
    ipsi = (out["left"][0] + out["right"][1]) / 2
    return times, contra, ipsi


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)
    subjects = list(range(1, args.subjects + 1))
    bnames = list(BANDS)

    curves = {b: [] for b in bnames}
    times = None
    for s in subjects:
        print(f"subject {s}...", flush=True)
        epochs, _ = preprocess(s, allow_confirmatory=args.allow_confirmatory, window=WINDOW)
        for b, band in BANDS.items():
            times, contra, ipsi = erd_curves(epochs, band)
            curves[b].append((contra, ipsi))

    plt.rcParams.update({"font.family": "sans-serif", "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    ncol = len(subjects) + 1
    fig, axes = plt.subplots(len(bnames), ncol, figsize=(1.9 * ncol, 2.9 * len(bnames)), squeeze=False, sharex=True)
    for i, b in enumerate(bnames):
        group = [np.mean([c[0] for c in curves[b]], axis=0), np.mean([c[1] for c in curves[b]], axis=0)]
        allv = np.concatenate([np.concatenate(c) for c in curves[b]])
        ylim = (np.percentile(allv, 1) - 5, np.percentile(allv, 99) + 5)
        for j in range(ncol):
            ax = axes[i, j]
            contra, ipsi = (group if j == len(subjects) else curves[b][j])
            ax.axvspan(*BASELINE, color=GRID, alpha=0.6, lw=0)
            ax.axvspan(TMIN, TMAX, color="#cde2fb", alpha=0.35, lw=0)
            ax.axvline(0, color=MUTED, lw=0.8)
            ax.axhline(0, color=MUTED, lw=0.5)
            ax.plot(times, ipsi, color=IPSI, lw=1.5, label="ipsilateral")
            ax.plot(times, contra, color=CONTRA, lw=1.5, label="contralateral")
            ax.set_ylim(*ylim)
            ax.set_xlim(CROP)
            ax.grid(axis="y", color=GRID, lw=0.8)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7)
            if i == 0:
                ax.set_title("mean of 10" if j == len(subjects) else f"S{subjects[j]}", fontsize=10)
            if j == 0:
                ax.set_ylabel(f"{b}\nERD% vs rest", fontsize=8)
            if i == len(bnames) - 1:
                ax.set_xlabel("s from cue", fontsize=7)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, frameon=False, fontsize=10)
    fig.text(0.5, 0.0, "Gray band: rest reference (-2 to -1 s). Blue band: frozen classification window (0.5-3.5 s). "
             "Vertical line: cue. Contralateral = C4 for left, C3 for right imagery. Same y-axis within each row.\n"
             "Predicted: contralateral drops below ipsilateral after the cue.", ha="center", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(RESULTS_DIR / "week2_erd_timecourse.png", dpi=130)
    plt.close(fig)

    lines = ["contra minus ipsi ERD% (percentage points, mean over the window; negative = as predicted)",
             "subject\tband\t" + "\t".join(CONTRAST_WINDOWS)]
    counts = {b: {w: 0 for w in CONTRAST_WINDOWS} for b in bnames}
    for b in bnames:
        for k, s in enumerate(subjects):
            contra, ipsi = curves[b][k]
            vals = []
            for w, (lo, hi) in CONTRAST_WINDOWS.items():
                m = (times >= lo) & (times <= hi)
                d = (contra[m] - ipsi[m]).mean()
                counts[b][w] += d < 0
                vals.append(f"{d:+.1f}")
            lines.append(f"{s}\t{b}\t" + "\t".join(vals))
    lines.append("")
    for b in bnames:
        gm = []
        for lo, hi in CONTRAST_WINDOWS.values():
            m = (times >= lo) & (times <= hi)
            gm.append(np.mean([(c[0][m] - c[1][m]).mean() for c in curves[b]]))
        lines.append(f"{b}: mean over subjects of contra minus ipsi: " +
                     ", ".join(f"{w} = {v:+.1f}" for w, v in zip(CONTRAST_WINDOWS, gm)))
    for b in bnames:
        lines.append(f"{b}: subjects with the predicted sign (contra below ipsi), of {len(subjects)}: " +
                     ", ".join(f"{w} = {counts[b][w]}" for w in CONTRAST_WINDOWS))
    lines.append(f"Descriptive only, exploratory subjects 1-{len(subjects)}, no test. Rest reference {BASELINE} s; "
                 f"wavelets n_cycles = f/2; window {WINDOW} s cropped to {CROP} s.")
    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week2_erd_timecourse.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
