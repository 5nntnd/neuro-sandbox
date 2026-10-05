"""Week 2: did we mix up channels? Two label-light checks on subjects 1-10 (no classifier).

Run (from the repo root, with the virtual environment active):
    python experiments/week2_channel_check.py

A. Neighbour correlation (task-independent). EEG from nearby electrodes correlates strongly through
   volume conduction. For each channel, take the mean correlation of its 8-30 Hz signal (frozen epochs,
   concatenated) with its 4 nearest electrodes by montage position. A channel whose label belongs to a
   far-away electrode would correlate poorly with its labelled neighbours. Report C3, C4 and the lowest
   channels per subject.

B. Best channel pair for the left/right effect. For each channel, Welch t of log10 band power
   (right minus left imagery). A pair (a, b) scores t[b] - t[a] (the same direction as LI = C4 - C3, where
   b should sit over right and a over left motor cortex). Over ALL ordered pairs the best score is
   simply max(t) - min(t). Its p-value comes from permuting the left/right labels, which accounts for
   searching 60+ x 60+ pairs. Also report where the C3/C4 pair ranks. If a mix-up explained a subject's
   weak C3/C4 effect, a different pair near the motor strip would stand out beyond the permutation null.

Descriptive only, exploratory subjects 1-10.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import RESULTS_DIR  # noqa: E402
from week2_band_power import BANDS, band_log_power  # noqa: E402
from week2_preprocess import N_EXPLORATORY, preprocess  # noqa: E402

N_NEIGHBOURS = 4
N_PERM = 2000
SEED = 0


def neighbour_correlation(epochs):
    data = np.concatenate(list(epochs.get_data()), axis=1)  # (channels, epochs * samples)
    corr = np.corrcoef(data)
    pos = np.array([ch["loc"][:3] for ch in epochs.info["chs"]])
    dist = np.linalg.norm(pos[:, None] - pos[None], axis=2)
    np.fill_diagonal(dist, np.inf)
    nn = np.argsort(dist, axis=1)[:, :N_NEIGHBOURS]
    return np.array([corr[i, nn[i]].mean() for i in range(len(pos))])


def welch_t(lp, is_right):
    r, l = lp[is_right], lp[~is_right]
    se = np.sqrt(r.var(axis=0, ddof=1) / len(r) + l.var(axis=0, ddof=1) / len(l))
    return (r.mean(axis=0) - l.mean(axis=0)) / se


def pair_check(lp, is_right, names, rng):
    i3, i4 = names.index("C3"), names.index("C4")
    t = welch_t(lp, is_right)
    best_b, best_a = int(np.argmax(t)), int(np.argmin(t))
    obs_best = t[best_b] - t[best_a]
    obs_c = t[i4] - t[i3]
    scores = t[None, :] - t[:, None]  # [a, b] = t[b] - t[a]
    off = ~np.eye(len(t), dtype=bool)
    rank = int((scores[off] >= obs_c).sum())  # 1 = C3->C4 is the best ordered pair
    n_pairs = int(off.sum())
    null_best, null_c = np.empty(N_PERM), np.empty(N_PERM)
    for k in range(N_PERM):
        tp = welch_t(lp, rng.permutation(is_right))
        null_best[k] = tp.max() - tp.min()
        null_c[k] = tp[i4] - tp[i3]
    p_best = (np.sum(null_best >= obs_best) + 1) / (N_PERM + 1)
    p_c = (np.sum(null_c >= obs_c) + 1) / (N_PERM + 1)  # one-sided, predicted direction
    return dict(best=f"{names[best_a]}->{names[best_b]}", best_score=obs_best, p_best=p_best,
                c_score=obs_c, c_rank=rank, n_pairs=n_pairs, p_c=p_c)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    a_lines = ["A. neighbour correlation (mean r with the 4 nearest electrodes, 8-30 Hz)",
               "subject\tC3\tC4\tmedian over channels\tlowest three channels"]
    b_lines = ["B. best ordered channel pair for (right - left) effect, t[b] - t[a]; p from label permutation over all pairs",
               "subject\tband\tbest pair a->b\tbest score\tp(best)\tC3->C4 score\tC3->C4 rank of n pairs\tp(C3->C4)"]
    for s in range(1, args.subjects + 1):
        print(f"subject {s}...", flush=True)
        epochs, _ = preprocess(s, allow_confirmatory=args.allow_confirmatory)
        names = epochs.ch_names
        nc = neighbour_correlation(epochs)
        low = np.argsort(nc)[:3]
        a_lines.append(f"{s}\t{nc[names.index('C3')]:.2f}\t{nc[names.index('C4')]:.2f}\t{np.median(nc):.2f}\t"
                       + ", ".join(f"{names[i]} ({nc[i]:.2f})" for i in low))
        is_right = epochs.events[:, 2] == epochs.event_id["right"]
        for bname, band in BANDS.items():
            r = pair_check(band_log_power(epochs, band), is_right, names, rng)
            b_lines.append(f"{s}\t{bname}\t{r['best']}\t{r['best_score']:.1f}\t{r['p_best']:.3f}\t{r['c_score']:+.1f}\t"
                           f"{r['c_rank']} of {r['n_pairs']}\t{r['p_c']:.3f}")
    text = "\n".join(a_lines + [""] + b_lines + ["",
        "Descriptive only, exploratory subjects, frozen epochs. p(best) accounts for searching all pairs; "
        "p(C3->C4) is one-sided in the predicted direction and uncorrected."])
    print(text)
    (RESULTS_DIR / "week2_channel_check.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
