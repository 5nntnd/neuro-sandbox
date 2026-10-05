"""Week 2: mu and beta band power for left vs right imagery (subjects 1-10, no classifier).

Run (from the repo root, with the virtual environment active):
    python experiments/week2_band_power.py

Prediction (hypothesis.md): imagining the right fist lowers power over left motor cortex (C3),
imagining the left fist lowers it over C4. So with LI = log10 power(C4) - log10 power(C3),
LI should be higher for right than for left trials. Effect = mean LI(right) - mean LI(left),
positive as predicted. Permutation p-values and bootstrap CIs are descriptive only (exploratory
subjects, 10 subjects x 2 bands, no correction); they are not the confirmatory test.

Band power is the mean Welch PSD over each band of the 0.5-3.5 s epochs (already 8-30 Hz filtered).

Figures (results/):
  week2_band_power_c3c4.png        C3/C4 power per subject, left vs right (crossing lines = predicted)
  week2_lateralization_forest.png  effect per subject with bootstrap 95% CI on one shared axis
  week2_topomaps.png               scalp map of log10 power, right minus left, per subject and group mean
"""
import argparse
import sys
from pathlib import Path

import matplotlib
import mne
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import RESULTS_DIR  # noqa: E402
from week2_preprocess import N_EXPLORATORY, preprocess  # noqa: E402

BANDS = {"mu (8-12 Hz)": (8, 12), "beta (13-30 Hz)": (13, 30)}
N_PERM = 5000
N_BOOT = 5000
SEED = 0
LEFT, RIGHT = "#2a78d6", "#eb6834"  # categorical slots 1 and 2 of the dataviz reference palette
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
SURFACE = "#fcfcfb"
# diverging blue <-> gray <-> red (dataviz reference): blue = lower for right imagery, red = higher
DIVERGING = LinearSegmentedColormap.from_list("div", ["#1c5cab", "#6da7ec", "#f0efec", "#ee8b8a", "#b02a2a"])


def band_log_power(epochs, band):
    """log10 mean PSD in the band, shape (epochs, channels), all EEG channels."""
    psd = epochs.compute_psd(method="welch", fmin=band[0], fmax=band[1], picks="eeg")
    return np.log10(psd.get_data().mean(axis=2))


def perm_p(li, is_right, rng):
    obs = li[is_right].mean() - li[~is_right].mean()
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        s = rng.permutation(is_right)
        null[i] = li[s].mean() - li[~s].mean()
    return obs, (np.sum(np.abs(null) >= abs(obs)) + 1) / (N_PERM + 1)


def boot_ci(li, is_right, rng):
    r, l = li[is_right], li[~is_right]
    d = np.array([rng.choice(r, r.size).mean() - rng.choice(l, l.size).mean() for _ in range(N_BOOT)])
    return np.percentile(d, [2.5, 97.5])


def style_axes(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    subjects = list(range(1, args.subjects + 1))
    bnames = list(BANDS)

    lines = ["subject\tband\tdropped\tn_left\tn_right\teffect (LI right - LI left)\t95% bootstrap CI\tperm p\tas predicted"]
    c3c4 = {}  # (subject, band) -> (mean_left, sem_left, mean_right, sem_right), each [C3, C4]
    stats = {b: [] for b in bnames}  # per band: (effect, lo, hi)
    chan_diff = {b: [] for b in bnames}  # per band: per subject {channel: right-left mean log power}
    infos = {}

    for s in subjects:
        print(f"subject {s}...", flush=True)
        epochs, dropped = preprocess(s, allow_confirmatory=args.allow_confirmatory)
        is_right = epochs.events[:, 2] == epochs.event_id["right"]
        names = epochs.ch_names
        i3, i4 = names.index("C3"), names.index("C4")
        infos[s] = (epochs.info, dropped)
        for bname, band in BANDS.items():
            lp = band_log_power(epochs, band)
            li = lp[:, i4] - lp[:, i3]
            eff, p = perm_p(li, is_right, rng)
            lo, hi = boot_ci(li, is_right, rng)
            stats[bname].append((eff, lo, hi))
            lines.append(f"{s}\t{bname}\t{','.join(dropped) or '-'}\t{(~is_right).sum()}\t{is_right.sum()}\t"
                         f"{eff:+.3f}\t[{lo:+.3f}, {hi:+.3f}]\t{p:.3f}\t{'yes' if eff > 0 else 'no'}")
            for cond, mask in (("left", ~is_right), ("right", is_right)):
                sub = lp[mask][:, [i3, i4]]
                c3c4[(s, bname, cond)] = (sub.mean(axis=0), sub.std(axis=0, ddof=1) / np.sqrt(mask.sum()))
            diff = lp[is_right].mean(axis=0) - lp[~is_right].mean(axis=0)
            chan_diff[bname].append(dict(zip(names, diff)))

    plt.rcParams.update({"font.family": "sans-serif", "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})

    # Figure 1: C3/C4 power per subject, left vs right
    fig, axes = plt.subplots(len(BANDS), len(subjects), figsize=(2.0 * len(subjects), 2.5 * len(BANDS)),
                             squeeze=False, sharex=True)
    for j, s in enumerate(subjects):
        for i, bname in enumerate(bnames):
            ax = axes[i, j]
            for cond, color in (("left", LEFT), ("right", RIGHT)):
                mean, sem = c3c4[(s, bname, cond)]
                ax.errorbar([0, 1], mean, yerr=sem, color=color, lw=2, marker="o", ms=6, capsize=0,
                            mec=SURFACE, mew=1.5, label=f"{cond} imagery")
            ax.set_xticks([0, 1], ["C3", "C4"])
            ax.set_xlim(-0.4, 1.4)
            style_axes(ax)
            if i == 0:
                ax.set_title(f"S{s}", fontsize=10, color=INK)
            if j == 0:
                ax.set_ylabel(f"{bname}\nlog10 power (V²/Hz)", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=10)
    fig.text(0.5, 0.005, "Mean ± SEM over trials. Each panel has its own y-axis. Predicted: lines cross "
             "(right imagery lower at C3, left imagery lower at C4).", ha="center", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(RESULTS_DIR / "week2_band_power_c3c4.png", dpi=130)
    plt.close(fig)

    # Figure 2: forest plot of the lateralization effect per subject, shared axis
    fig, axes = plt.subplots(1, len(BANDS), figsize=(9, 4.2), sharex=True, sharey=True)
    ys = np.arange(len(subjects))[::-1]
    for ax, bname in zip(axes, bnames):
        for y, (eff, lo, hi) in zip(ys, stats[bname]):
            sig = lo > 0 or hi < 0
            ax.plot([lo, hi], [y, y], color=INK if sig else MUTED, lw=1.5, solid_capstyle="round")
            ax.plot(eff, y, "o", ms=8, mfc=INK if sig else SURFACE, mec=INK if sig else MUTED, mew=1.5)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_yticks(ys, [f"S{s}" for s in subjects])
        ax.set_title(bname, fontsize=10)
        ax.set_xlabel("LI right − LI left (log10 units)", fontsize=9)
        ax.grid(axis="x", color=GRID, lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    axes[0].text(0.02, -0.28, "◀ opposite to prediction", transform=axes[0].transAxes, fontsize=8, color=MUTED)
    axes[1].text(0.98, -0.28, "as predicted ▶", transform=axes[1].transAxes, fontsize=8, color=MUTED, ha="right")
    fig.suptitle("Filled marker: 95% bootstrap CI excludes 0. Open marker: it includes 0.", fontsize=9, color=MUTED, y=0.0)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(RESULTS_DIR / "week2_lateralization_forest.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Figure 3: scalp maps of right minus left log power, per subject and group mean
    template_s = next((s for s in subjects if not infos[s][1]), subjects[0])
    template = infos[template_s][0]
    fig, axes = plt.subplots(len(BANDS), len(subjects) + 1, figsize=(1.9 * (len(subjects) + 1), 2.6 * len(BANDS)),
                             squeeze=False)
    for i, bname in enumerate(bnames):
        subj_vmax = max(np.nanpercentile(np.abs(list(d.values())), 98) for d in chan_diff[bname])
        group = np.array([[d.get(ch, np.nan) for ch in template.ch_names] for d in chan_diff[bname]])
        gmean = np.nanmean(group, axis=0)
        g_vmax = np.nanmax(np.abs(gmean))
        for j, s in enumerate(subjects + ["mean"]):
            ax = axes[i, j]
            if s == "mean":
                data, info, vmax = gmean, template, g_vmax
            else:
                info = infos[s][0]
                data = np.array([chan_diff[bname][j][ch] for ch in info.ch_names])
                vmax = subj_vmax
            mask = np.array([ch in ("C3", "C4") for ch in info.ch_names])
            mne.viz.plot_topomap(data, info, axes=ax, show=False, cmap=DIVERGING, vlim=(-vmax, vmax), contours=0,
                                 sensors=False, mask=mask,
                                 mask_params=dict(marker="o", markerfacecolor="none", markeredgecolor=INK,
                                                  markeredgewidth=1.2, markersize=5))
            if i == 0:
                ax.set_title("S" + str(s) if s != "mean" else "mean of 10", fontsize=10, color=INK)
            if j == 0:
                ax.set_ylabel(bname, fontsize=9)
            ax.text(0.5, -0.08, f"±{vmax:.2f}", transform=ax.transAxes, ha="center", va="top", fontsize=7, color=MUTED)
    fig.text(0.5, 0.0, "log10 power, right minus left imagery (circles = C3 left, C4 right; colour scale ± value under each map; "
             "subjects share a scale, the mean has its own).\nPredicted over motor cortex: blue at C3 (left side), red at C4 (right side).",
             ha="center", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(RESULTS_DIR / "week2_topomaps.png", dpi=130)
    plt.close(fig)

    lines.append("")
    for bname in bnames:
        e = np.array([x[0] for x in stats[bname]])
        n_ci = sum(1 for _, lo, hi in stats[bname] if lo > 0)
        n_ci_opp = sum(1 for _, lo, hi in stats[bname] if hi < 0)
        lines.append(f"{bname}: {int((e > 0).sum())} of {len(e)} subjects have the predicted sign; "
                     f"{n_ci} have a CI wholly above 0, {n_ci_opp} wholly below 0; "
                     f"median effect {np.median(e):+.3f} (log10 units; +0.1 = 26% more C4 than C3 power)")
    lines.append("Exploratory subjects only; permutation p-values and bootstrap CIs are uncorrected and descriptive. "
                 "Epochs: frozen preprocessing (week2_preprocess.py), 45 trials per subject, no rejection. "
                 f"Group topomap uses template channels of subject {template_s}; dropped channels are left out of the mean for that subject.")
    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week2_band_power.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
