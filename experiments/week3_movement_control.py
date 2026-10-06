"""Week 3 positive control: the frozen CSP + LDA pipeline on REAL left/right fist movement (runs 3, 7, 11).

Run (repo root, venv active):
    .venv\\Scripts\\python experiments\\week3_movement_control.py [--perms 1000] [--jobs -1]

Diagnostic only (reference/hypothesis.md, 2026-10-06): same preprocessing, CSP, LDA, leave-one-run-out,
permutation test and pattern check as week3_csp_lda.py, only the runs differ. Subjects 1-10 only.
Compares with the imagery result in results/week3_csp_lda.txt.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week2_preprocess import N_EXPLORATORY, preprocess  # noqa: E402
from week3_csp_lda import (PASS_ACC, PASS_P, RESULTS_DIR, RUN_SAMPLES, SEED,  # noqa: E402
                           pattern_summary, perm_acc, score)

MOVEMENT_RUNS = [3, 7, 11]  # real left vs right fist (T1 = left, T2 = right)


def imagery_table():
    """accuracy per subject from the committed imagery output, for comparison."""
    text = (RESULTS_DIR / "week3_csp_lda.txt").read_text().splitlines()
    out = {}
    for line in text:
        m = re.match(r"\s*(\d+)\s+(\d\.\d\d)\s", line)
        if m:
            out.setdefault(int(m.group(1)), float(m.group(2)))  # first table only; the pattern table follows it
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--perms", type=int, default=1000)
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()
    lines = []

    def say(text=""):
        print(text, flush=True)
        lines.append(text)

    imagery = imagery_table()
    say(f"week3_movement_control {datetime.date.today()} | mne {mne.__version__}, seed {SEED}, "
        f"{args.perms} permutations, runs {MOVEMENT_RUNS} (real movement)")
    say("Same frozen pipeline as week3_csp_lda.py; positive control, not a result for the hypothesis.")
    say()
    say(f"{'subj':>4} {'acc':>5} {'95% CI':>11} {'kappa':>6} {'perm p':>7} {'det':>4} | imagery acc | dropped")

    rows, patterns = [], {}
    for subject in range(1, N_EXPLORATORY + 1):
        epochs, dropped = preprocess(subject, runs=MOVEMENT_RUNS)
        X, y = epochs.get_data(), epochs.events[:, 2]
        groups = epochs.events[:, 0] // RUN_SAMPLES
        assert sorted(set(groups)) == [0, 1, 2], f"subject {subject}: run split failed"
        acc, lo, hi, kappa = score(X, y, groups)
        seeds = np.random.SeedSequence(SEED + 100 + subject).generate_state(args.perms)
        null = np.array(Parallel(n_jobs=args.jobs)(delayed(perm_acc)(X, y, groups, int(s)) for s in seeds))
        p = (1 + np.sum(null >= acc - 1e-12)) / (1 + args.perms)
        detected = acc >= PASS_ACC and p < PASS_P
        csp, share, expected, top = pattern_summary(epochs, X, y)
        patterns[subject] = (csp, epochs.info, share, expected, top)
        rows.append(dict(subject=subject, acc=acc, lo=lo, hi=hi, detected=detected))
        say(f"{subject:>4} {acc:>5.2f} {lo:>5.2f}-{hi:<5.2f} {kappa:>6.2f} {p:>7.3f} "
            f"{'yes' if detected else 'no':>4} | {imagery.get(subject, float('nan')):>11.2f} | "
            f"{', '.join(dropped) or 'none'}")

    n_det = sum(r["detected"] for r in rows)
    say()
    say(f"{n_det}/10 subjects pass the numeric rule on real movement "
        f"(median accuracy {np.median([r['acc'] for r in rows]):.2f}; imagery median 0.62).")
    say()
    say("Pattern weight by region (share of summed |pattern|, 4 components; in brackets the even-spread share):")
    say(f"{'subj':>4} {'motor':>13} {'frontal':>13} {'temporal':>13} {'other':>13} | top 5 channels")
    for subject, (_, _, share, expected, top) in patterns.items():
        cells = " ".join(f"{share[r]:>5.2f} ({expected[r]:.2f})" for r in ("motor", "frontal", "temporal", "other"))
        say(f"{subject:>4} {cells} | {', '.join(top)}")

    RESULTS_DIR.mkdir(exist_ok=True)
    xs = np.array([r["subject"] for r in rows])
    acc = np.array([r["acc"] for r in rows])
    lo = np.array([r["lo"] for r in rows])
    hi = np.array([r["hi"] for r in rows])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0.5, color="0.4", ls=":", lw=1)
    ax.axhline(PASS_ACC, color="tab:red", ls="--", lw=1, label=f"{PASS_ACC:.0%} threshold")
    ax.errorbar(xs, acc, yerr=[acc - lo, hi - acc], fmt="none", ecolor="0.5", capsize=3)
    ax.scatter(xs, acc, c=["tab:green" if r["detected"] else "tab:blue" for r in rows], zorder=3,
               label="real movement")
    ax.plot(xs, [imagery.get(s, np.nan) for s in xs], "D", color="0.55", mfc="none", label="imagery (Week 3)")
    ax.set(xlabel="subject", ylabel="leave-one-run-out accuracy", ylim=(0.2, 1.0), xticks=xs,
           title=f"Positive control: real fist movement, same pipeline ({n_det} pass: green)")
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week3_movement_control_accuracy.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 10, figsize=(19, 4.4), squeeze=False)
    for col, (subject, (csp, info, *_)) in enumerate(patterns.items()):
        for row, comp in enumerate((0, 3)):
            mne.viz.plot_topomap(csp.patterns_[comp], info, axes=axes[row, col], show=False,
                                 sensors=False, contours=0)
        axes[0, col].set_title(f"s{subject}", fontsize=9)
    axes[0, 0].set_ylabel("component 1", fontsize=8)
    axes[1, 0].set_ylabel("component 4", fontsize=8)
    fig.suptitle("CSP patterns, real movement (fitted on all 45 trials, display only)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week3_movement_control_patterns.png", dpi=150)
    plt.close(fig)

    (RESULTS_DIR / "week3_movement_control.txt").write_text("\n".join(lines) + "\n")
    print(f"Saved week3_movement_control.txt and two figures in {RESULTS_DIR}")


if __name__ == "__main__":
    main()
