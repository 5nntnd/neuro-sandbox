"""Week 3: CSP + LDA, leave-one-run-out CV, subjects 1-10 (exploratory set only).

Run (repo root, venv active):
    .venv\\Scripts\\python experiments\\week3_csp_lda.py [--perms 1000] [--subjects 10] [--jobs -1]

Pipeline is frozen in reference/hypothesis.md: preprocess() from week2_preprocess.py, then
CSP(4 components, reg='ledoit_wolf') -> LDA, CSP refit inside every training fold.
Per subject: pooled held-out accuracy, exact 95% CI, Cohen's kappa, permutation p
(labels shuffled within each run, whole CV repeated), dropped channels.
Robustness (secondary only): same run with the flagged channels kept, no permutation test.
Artifact check: CSP patterns (fitted on all 45 trials, for display only) and the share of
pattern weight over sensorimotor channels versus frontal and temporal ones.
Refuses subjects above 10.
"""
import argparse
import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
import sklearn
from joblib import Parallel, delayed
from mne.decoding import CSP
from scipy.stats import binomtest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import make_pipeline

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week2_preprocess import N_EXPLORATORY, preprocess  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
SEED = 0
RUN_SAMPLES = 20000  # each PhysioNet run is 125 s at 160 Hz; runs are concatenated in order
PASS_ACC, PASS_P = 0.64, 0.05  # "detected" per subject, reference/hypothesis.md

# Fixed a priori channel groups for the artifact check (not chosen from results).
MOTOR = {"FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2", "C4", "C6",
         "CP3", "CP1", "CPz", "CP2", "CP4"}


def region(name):
    if name in MOTOR:
        return "motor"
    if name.startswith(("Fp", "AF", "F")) and not name.startswith(("FC", "FT")):
        return "frontal"
    if name.startswith(("T", "FT", "TP")):
        return "temporal"
    return "other"


def make_clf():
    return make_pipeline(CSP(n_components=4, reg="ledoit_wolf", log=True), LDA())


def cv_predict(X, y, groups):
    pred = np.empty_like(y)
    for train, test in LeaveOneGroupOut().split(X, y, groups):
        pred[test] = make_clf().fit(X[train], y[train]).predict(X[test])
    return pred


def permuted(y, groups, rng):
    out = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        out[idx] = rng.permutation(y[idx])
    return out


def perm_acc(X, y, groups, seed):
    """Accuracy of the whole CV on labels shuffled within each run."""
    yp = permuted(y, groups, np.random.default_rng(seed))
    return (cv_predict(X, yp, groups) == yp).mean()


def load(subject, drop_flagged):
    epochs, dropped = preprocess(subject, drop_flagged=drop_flagged)
    X = epochs.get_data()
    y = epochs.events[:, 2]
    groups = epochs.events[:, 0] // RUN_SAMPLES
    assert sorted(set(groups)) == [0, 1, 2], f"subject {subject}: run split failed {set(groups)}"
    return epochs, X, y, groups, dropped


def score(X, y, groups):
    pred = cv_predict(X, y, groups)
    n = len(y)
    k = int((pred == y).sum())
    ci = binomtest(k, n, 0.5).proportion_ci(method="exact")
    return k / n, ci.low, ci.high, cohen_kappa_score(y, pred)


def pattern_summary(epochs, X, y):
    csp = CSP(n_components=4, reg="ledoit_wolf", log=True).fit(X, y)
    names = epochs.ch_names
    w = np.abs(csp.patterns_[:4]).sum(axis=0)  # (n_channels,)
    w = w / w.sum()
    regions = np.array([region(n) for n in names])
    share = {r: float(w[regions == r].sum()) for r in ("motor", "frontal", "temporal", "other")}
    expected = {r: float((regions == r).mean()) for r in share}
    top = [names[i] for i in np.argsort(w)[::-1][:5]]
    return csp, share, expected, top


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY)
    parser.add_argument("--perms", type=int, default=1000)
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY:
        parser.error("Subjects above 10 are the confirmatory set; this script does not run them.")

    lines = []

    def say(text=""):
        print(text, flush=True)
        lines.append(text)

    say(f"week3_csp_lda {datetime.date.today()} | mne {mne.__version__}, scikit-learn "
        f"{sklearn.__version__}, seed {SEED}, {args.perms} permutations")
    say("CSP 4 comp, reg=ledoit_wolf -> LDA, leave-one-run-out, pooled held-out predictions.")
    say(f"detected = accuracy >= {PASS_ACC:.2f} and permutation p < {PASS_P}")
    say()
    say(f"{'subj':>4} {'acc':>5} {'95% CI':>11} {'kappa':>6} {'perm p':>7} {'det':>4} | "
        f"{'kept-all acc':>12} {'kappa':>6} | dropped")

    rows, patterns = [], {}
    for subject in range(1, args.subjects + 1):
        epochs, X, y, groups, dropped = load(subject, drop_flagged=True)
        acc, lo, hi, kappa = score(X, y, groups)
        seeds = np.random.SeedSequence(SEED + subject).generate_state(args.perms)
        null = np.array(Parallel(n_jobs=args.jobs)(
            delayed(perm_acc)(X, y, groups, int(s)) for s in seeds))
        p = (1 + np.sum(null >= acc - 1e-12)) / (1 + args.perms)
        detected = acc >= PASS_ACC and p < PASS_P

        _, X2, y2, g2, _ = load(subject, drop_flagged=False)
        acc2, _, _, kappa2 = score(X2, y2, g2)

        csp, share, expected, top = pattern_summary(epochs, X, y)
        patterns[subject] = (csp, epochs.info, share, expected, top)
        rows.append(dict(subject=subject, acc=acc, lo=lo, hi=hi, kappa=kappa, p=p,
                         detected=detected, acc_kept=acc2, share=share, top=top))
        say(f"{subject:>4} {acc:>5.2f} {lo:>5.2f}-{hi:<5.2f} {kappa:>6.2f} {p:>7.3f} "
            f"{'yes' if detected else 'no':>4} | {acc2:>12.2f} {kappa2:>6.2f} | "
            f"{', '.join(dropped) or 'none'}")

    n_det = sum(r["detected"] for r in rows)
    say()
    say(f"{n_det}/{len(rows)} exploratory subjects pass the per-subject rule "
        f"(median accuracy {np.median([r['acc'] for r in rows]):.2f}).")
    say("Note: subjects 1-10 are exploratory; the group claim needs the confirmatory set.")

    say()
    say("Where the CSP patterns put their weight (share of summed |pattern| over 4 components;"
        " in brackets the share expected if weight were spread evenly over channels):")
    say(f"{'subj':>4} {'motor':>13} {'frontal':>13} {'temporal':>13} {'other':>13} | top 5 channels")
    for subject, (_, _, share, expected, top) in patterns.items():
        cells = " ".join(f"{share[r]:>5.2f} ({expected[r]:.2f})" for r in
                         ("motor", "frontal", "temporal", "other"))
        say(f"{subject:>4} {cells} | {', '.join(top)}")

    RESULTS_DIR.mkdir(exist_ok=True)

    # Figure 1: accuracy with CI.
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = np.array([r["subject"] for r in rows])
    acc = np.array([r["acc"] for r in rows])
    lo = np.array([r["lo"] for r in rows])
    hi = np.array([r["hi"] for r in rows])
    ax.axhline(0.5, color="0.4", ls=":", lw=1)
    ax.axhline(PASS_ACC, color="tab:red", ls="--", lw=1, label=f"{PASS_ACC:.0%} threshold")
    colors = ["tab:green" if r["detected"] else "tab:blue" for r in rows]
    ax.errorbar(xs, acc, yerr=[acc - lo, hi - acc], fmt="none", ecolor="0.5", capsize=3)
    ax.scatter(xs, acc, c=colors, zorder=3)
    ax.plot(xs, [r["acc_kept"] for r in rows], "D", color="0.55", mfc="none",
            label="flagged channels kept (robustness)")
    ax.set(xlabel="subject", ylabel="leave-one-run-out accuracy", ylim=(0.2, 1.0), xticks=xs,
           title=f"Week 3: CSP + LDA, subjects 1-10 ({n_det} pass: green)")
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week3_csp_lda_accuracy.png", dpi=150)
    plt.close(fig)

    # Figure 2: CSP patterns, first and last component (the two extreme filters).
    n = len(patterns)
    fig, axes = plt.subplots(2, n, figsize=(1.9 * n, 4.4), squeeze=False)
    for col, (subject, (csp, info, *_)) in enumerate(patterns.items()):
        for row, comp in enumerate((0, 3)):
            mne.viz.plot_topomap(csp.patterns_[comp], info, axes=axes[row, col], show=False,
                                 sensors=False, contours=0)
        axes[0, col].set_title(f"s{subject}", fontsize=9)
    axes[0, 0].set_ylabel("component 1", fontsize=8)
    axes[1, 0].set_ylabel("component 4", fontsize=8)
    fig.suptitle("CSP patterns (fitted on all 45 trials, display only)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week3_csp_patterns.png", dpi=150)
    plt.close(fig)

    (RESULTS_DIR / "week3_csp_lda.txt").write_text("\n".join(lines) + "\n")
    print(f"Saved week3_csp_lda.txt and two figures in {RESULTS_DIR}")


if __name__ == "__main__":
    main()
