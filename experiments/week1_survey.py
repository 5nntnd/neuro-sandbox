"""Week 1: survey data quality across the exploratory subjects, no classifier.

Run (from the repo root, with the virtual environment active):
    python experiments/week1_survey.py [--subjects 10]

Per subject: 60 Hz noise, eye components from ICA (diagnostic only, nothing is removed),
flat or noisy channels, trial counts and whether every cue lasts long enough for the
frozen 0.5-3.5 s epoch window, and muscle (30-55 Hz) power including whether it differs
between left and right trials, which is the way muscle could fake a decoding result.

Subjects above 10 are the confirmatory set (see reference/hypothesis.md) and are refused
unless --allow-confirmatory is passed.
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.preprocessing import ICA
from scipy.stats import ttest_ind

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_inspect_raw import EYE_PROXY, RESULTS_DIR, SEED, line_noise_report, load_raw  # noqa: E402

TMIN, TMAX = 0.5, 3.5  # frozen epoch window, see reference/hypothesis.md
EMG_BAND = (30, 55)  # stops below the 60 Hz mains line
N_EXPLORATORY = 10

mne.set_log_level("ERROR")


def survey_subject(subject):
    raw = load_raw(subject)
    raw.set_eeg_reference("average", projection=False)  # frozen pipeline choice
    row = {"subject": subject}

    noise, _, _ = line_noise_report(raw, [60])
    row["line60_db"] = float(noise[0].split("is ")[1].split(" dB")[0])

    # events and timing: T1 = left, T2 = right (valid for runs 4, 8, 12 only)
    ann = raw.annotations
    cue = [(d, desc) for d, desc in zip(ann.duration, ann.description) if desc in ("T1", "T2")]
    row["n_left"] = sum(desc == "T1" for _, desc in cue)
    row["n_right"] = sum(desc == "T2" for _, desc in cue)
    row["min_cue_s"] = min(d for d, _ in cue)

    # ICA, diagnostic only
    ica_raw = raw.copy().filter(1, 40)
    ica = ICA(n_components=20, random_state=SEED, max_iter=800)
    ica.fit(ica_raw)
    eog_idx, _ = ica.find_bads_eog(ica_raw, ch_name=EYE_PROXY, verbose=False)
    row["eye_components"] = len(set(eog_idx))

    # flat or noisy channels: robust spread of channel standard deviations
    std = ica_raw.get_data(picks="eeg").std(axis=1)
    med = np.median(std)
    bad = [ica_raw.ch_names[i] for i in np.where((std < 0.2 * med) | (std > 5 * med))[0]]
    row["odd_channels"] = ",".join(bad) if bad else "-"

    # muscle: 30-55 Hz power per channel, and left-vs-right difference per channel
    emg = raw.copy().filter(*EMG_BAND)
    events, event_id = mne.events_from_annotations(emg, event_id=dict(T1=2, T2=3))
    epochs = mne.Epochs(emg, events, dict(left=2, right=3), tmin=TMIN, tmax=TMAX,
                        baseline=None, preload=True)
    power = np.log10((epochs.get_data(picks="eeg") ** 2).mean(axis=2))  # trials x channels
    labels = epochs.events[:, 2]
    t, p = ttest_ind(power[labels == 2], power[labels == 3], axis=0)
    row["emg_sig_channels"] = int((p < 0.05).sum())  # about 3 of 64 expected by chance
    row["emg_max_abs_t"] = float(np.abs(t).max())
    mean_power = power.mean(axis=0)
    row["emg_top_channels"] = ",".join(epochs.ch_names[i] for i in np.argsort(mean_power)[::-1][:3])
    return row, mean_power, epochs.info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=N_EXPLORATORY, help="survey subjects 1..N")
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if args.subjects > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    RESULTS_DIR.mkdir(exist_ok=True)

    rows, powers, info = [], [], None
    for s in range(1, args.subjects + 1):
        print(f"subject {s}...", flush=True)
        row, mean_power, info = survey_subject(s)
        rows.append(row)
        powers.append(mean_power)

    cols = ["subject", "n_left", "n_right", "min_cue_s", "line60_db", "eye_components",
            "odd_channels", "emg_sig_channels", "emg_max_abs_t", "emg_top_channels"]
    lines = ["\t".join(cols)]
    for r in rows:
        lines.append("\t".join(f"{r[c]:.1f}" if isinstance(r[c], float) else str(r[c]) for c in cols))
    lines += [
        "",
        f"mne {mne.__version__}; average reference; epoch window {TMIN}-{TMAX} s; "
        f"EMG band {EMG_BAND[0]}-{EMG_BAND[1]} Hz (log10 power per trial).",
        "emg_sig_channels = channels with p < 0.05 for left vs right muscle-band power "
        "(about 3 of 64 expected by chance); odd_channels = std below 0.2x or above 5x the median.",
    ]
    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week1_survey.txt").write_text(text + "\n", encoding="utf-8")

    lo, hi = np.min(powers), np.max(powers)  # one colour scale for all subjects
    fig, axes = plt.subplots(2, (len(rows) + 1) // 2, figsize=(2.6 * ((len(rows) + 1) // 2), 5.4))
    for ax, s, pw in zip(axes.ravel(), range(1, len(rows) + 1), powers):
        im, _ = mne.viz.plot_topomap(pw, info, axes=ax, show=False, cmap="viridis", vlim=(lo, hi), contours=0)
        ax.set_title(f"S{s}", fontsize=9)
    fig.colorbar(im, ax=axes, shrink=0.6, label="log10 power (V²)")
    fig.suptitle("Mean log10 power, 30-55 Hz (muscle band), epochs 0.5-3.5 s", fontsize=10)
    fig.savefig(RESULTS_DIR / "week1_emg_topomaps.png", dpi=110)


if __name__ == "__main__":
    main()
