"""Week 0: see how noisy EEG decoding accuracy is with few trials.

Setup (once, from the repo root):
    python -m venv .venv
    .venv\\Scripts\\activate
    pip install -r requirements.txt

Run:
    python experiments/week0_noise_check.py [--subjects 10] [--perms 200] [--focus 1]

Data downloads go to data/ and the figure goes to outputs/ (both gitignored).

Dataset: PhysioNet EEG Motor Movement/Imagery, runs 4, 8, 12 = imagined left vs
right fist, roughly 45 trials per subject. Cross-validation is leave-one-run-out
(PhysioNet has a single session, so runs are the honest split). A shuffled 5-fold
score is shown too, to see how much plain random splitting flatters the result.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.datasets import eegbci
from mne.decoding import CSP
from scipy.stats import binom, binomtest
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
RUNS = [4, 8, 12]  # imagined left vs right fist
SEED = 0

mne.set_log_level("ERROR")


def load_subject(subject):
    """Return epochs (n_trials, n_channels, n_times), labels, and run index per trial."""
    DATA_DIR.mkdir(exist_ok=True)
    paths = eegbci.load_data(subject, RUNS, path=str(DATA_DIR), update_path=False)
    Xs, ys, groups = [], [], []
    for run_index, path in enumerate(paths):
        raw = mne.io.read_raw_edf(path, preload=True)
        eegbci.standardize(raw)
        raw.set_montage("standard_1005")
        raw.filter(8, 30)
        events, _ = mne.events_from_annotations(raw, event_id=dict(T1=2, T2=3))
        epochs = mne.Epochs(raw, events, dict(left=2, right=3),
                            tmin=0.5, tmax=3.5, baseline=None, preload=True)
        Xs.append(epochs.get_data())
        ys.append(epochs.events[:, 2])
        groups.append(np.full(len(epochs), run_index))
    return np.concatenate(Xs), np.concatenate(ys), np.concatenate(groups)


def make_clf():
    return make_pipeline(CSP(n_components=4), LDA())


def runwise_accuracy(X, y, groups):
    """Leave-one-run-out accuracy, pooled over all held-out trials."""
    pred = np.empty_like(y)
    for train, test in LeaveOneGroupOut().split(X, y, groups):
        pred[test] = make_clf().fit(X[train], y[train]).predict(X[test])
    return (pred == y).mean()


def shuffled_kfold_accuracy(X, y, n_seeds=5):
    """Plain shuffled 5-fold, averaged over a few seeds. Leaks slow drift between trials."""
    scores = []
    for seed in range(n_seeds):
        cv = StratifiedKFold(5, shuffle=True, random_state=seed)
        scores.append(cross_val_score(make_clf(), X, y, cv=cv).mean())
    return float(np.mean(scores))


def permuted_labels(y, groups, rng):
    """Shuffle labels within each run, so the run structure is preserved."""
    y_perm = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        y_perm[idx] = rng.permutation(y[idx])
    return y_perm


def significance_threshold(n):
    """Smallest accuracy that beats 50% chance at one-sided p < 0.05 for n trials."""
    return (binom.isf(0.05, n, 0.5) + 1) / n


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subjects", type=int, default=10, help="analyse subjects 1..N")
    parser.add_argument("--perms", type=int, default=200, help="label permutations for panel A")
    parser.add_argument("--focus", type=int, default=1, help="subject shown in panel A")
    args = parser.parse_args()
    if not 1 <= args.focus <= args.subjects:
        parser.error("--focus must be between 1 and --subjects")
    rng = np.random.default_rng(SEED)

    results = []
    focus = None
    print(f"{'subj':>4} {'n':>4} {'run-wise':>9} {'95% CI':>15} {'need':>6} {'shuffled':>9}")
    for subject in range(1, args.subjects + 1):
        X, y, groups = load_subject(subject)
        n = len(y)
        acc = runwise_accuracy(X, y, groups)
        k = int(round(acc * n))
        ci = binomtest(k, n, 0.5).proportion_ci(method="exact")
        need = significance_threshold(n)
        shuffled = shuffled_kfold_accuracy(X, y)
        results.append(dict(subject=subject, n=n, acc=acc, lo=ci.low, hi=ci.high,
                            need=need, shuffled=shuffled))
        print(f"{subject:>4} {n:>4} {acc:>9.2f} {ci.low:>7.2f}-{ci.high:<7.2f} "
              f"{need:>6.2f} {shuffled:>9.2f}", flush=True)
        if subject == args.focus:
            focus = (X, y, groups, acc)

    X, y, groups, observed = focus
    print(f"\nPermutation test for subject {args.focus} ({args.perms} shuffles)...", flush=True)
    null = np.array([runwise_accuracy(X, permuted_labels(y, groups, rng), groups)
                     for _ in range(args.perms)])
    p_value = (1 + np.sum(null >= observed)) / (1 + args.perms)

    n_sig = sum(r["acc"] >= r["need"] for r in results)
    print(f"Subject {args.focus}: accuracy {observed:.2f}, permutation p = {p_value:.3f}")
    print(f"{n_sig}/{len(results)} subjects reach their own significance threshold.")

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 4.8),
                                     gridspec_kw=dict(width_ratios=[1, 1.4]))

    ax_a.hist(null, bins=np.linspace(0.2, 0.8, 25), color="0.7", edgecolor="white")
    ax_a.axvline(np.percentile(null, 95), color="tab:red", ls="--", lw=1,
                 label="95th percentile of chance")
    ax_a.axvline(observed, color="tab:blue", lw=2, label=f"real labels: {observed:.2f}")
    ax_a.set(xlabel="accuracy", ylabel=f"count of {args.perms} label shuffles",
             title=f"A. Subject {args.focus}: what chance looks like\n"
                   f"(n = {len(y)} trials, permutation p = {p_value:.3f})")
    ax_a.legend(frameon=False)

    xs = [r["subject"] for r in results]
    acc = np.array([r["acc"] for r in results])
    lo = np.array([r["lo"] for r in results])
    hi = np.array([r["hi"] for r in results])
    ax_b.axhline(0.5, color="0.4", ls=":", lw=1)
    ax_b.errorbar(xs, acc, yerr=[acc - lo, hi - acc], fmt="o", color="tab:blue",
                  capsize=3, label="run-wise accuracy, 95% CI")
    ax_b.plot(xs, [r["need"] for r in results], "_", color="tab:red", ms=14, mew=2,
              label="needed to beat chance (p<0.05)")
    ax_b.plot(xs, [r["shuffled"] for r in results], "D", color="0.55", mfc="none",
              label="shuffled 5-fold (leaky)")
    ax_b.set(xlabel="subject", ylabel="accuracy", ylim=(0.2, 1.0), xticks=xs,
             title=f"B. Every subject: {n_sig}/{len(results)} clear their own threshold")
    ax_b.legend(frameon=False, loc="upper right", fontsize=8)

    fig.suptitle("Week 0: how noisy is accuracy with ~45 trials? (imagined left vs right fist)")
    fig.tight_layout()
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / "week0_noise_check.png"
    fig.savefig(out, dpi=150)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
