"""Week 1: look at the raw EEG of one subject before any classifier.

Run (from the repo root, with the virtual environment active):
    python experiments/week1_inspect_raw.py [--subject 1]

Reports sampling rate, channels, events, line-noise peaks, and tries ICA to find
eye-blink components. No classifier is run here. Figures and the text summary go
to results/ (committed, linked from LOG.md); downloads go to the gitignored data/ folder.

Dataset: PhysioNet EEG Motor Movement/Imagery, runs 4, 8, 12 (imagined left vs right fist).
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.datasets import eegbci
from mne.preprocessing import ICA

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
RUNS = [4, 8, 12]
SEED = 0
EYE_PROXY = ["Fp1", "Fp2"]  # the dataset has no EOG channel, so frontal channels stand in

mne.set_log_level("ERROR")


def load_raw(subject):
    DATA_DIR.mkdir(exist_ok=True)
    paths = eegbci.load_data(subject, RUNS, path=str(DATA_DIR), update_path=False)
    raw = mne.concatenate_raws([mne.io.read_raw_edf(p, preload=True) for p in paths])
    eegbci.standardize(raw)
    raw.set_montage("standard_1005")
    return raw


def line_noise_report(raw, lines):
    """Peak-to-neighbour power ratio (dB) at each candidate mains frequency."""
    psd = raw.compute_psd(fmin=1, fmax=raw.info["sfreq"] / 2 - 1, picks="eeg")
    freqs = psd.freqs
    mean_psd = psd.get_data().mean(axis=0)
    out = []
    for f in lines:
        if f >= freqs[-1]:
            out.append(f"{f} Hz: above the {freqs[-1]:.0f} Hz usable range, cannot tell")
            continue
        peak = mean_psd[np.abs(freqs - f) <= 0.5].max()
        side = mean_psd[((freqs >= f - 5) & (freqs <= f - 2)) | ((freqs >= f + 2) & (freqs <= f + 5))]
        ratio = 10 * np.log10(peak / np.median(side)) if side.size else float("nan")
        out.append(f"{f} Hz: peak is {ratio:+.1f} dB above its neighbours")
    return out, freqs, mean_psd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=int, default=1)
    args = parser.parse_args()
    RESULTS_DIR.mkdir(exist_ok=True)
    lines = []

    raw = load_raw(args.subject)
    lines += [
        f"Subject {args.subject}, runs {RUNS}, mne {mne.__version__}",
        f"Sampling rate: {raw.info['sfreq']:.0f} Hz",
        f"EEG channels: {len(mne.pick_types(raw.info, eeg=True))}; "
        f"duration {raw.times[-1]:.0f} s",
        f"Hardware filters in file: highpass {raw.info['highpass']} Hz, lowpass {raw.info['lowpass']} Hz",
        f"Reference: not stored in the EDF files (MNE reports custom_ref_applied="
        f"{raw.info['custom_ref_applied']}); check the PhysioNet dataset page",
    ]
    events, event_id = mne.events_from_annotations(raw)
    counts = {name: int((events[:, 2] == code).sum()) for name, code in event_id.items()}
    lines.append(f"Annotation counts (T0 = rest, T1 = left, T2 = right): {counts}")

    noise_lines, freqs, mean_psd = line_noise_report(raw, [50, 60])
    lines += ["Line noise (raw, unfiltered): "] + [f"  {s}" for s in noise_lines]

    # Figure 1: mean PSD with mains candidates marked
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.semilogy(freqs, mean_psd)
    for f in (50, 60):
        ax.axvline(f, color="grey", ls="--", lw=0.8)
        ax.text(f, ax.get_ylim()[1], f" {f}", va="top", fontsize=8)
    ax.set(xlabel="Frequency (Hz)", ylabel="Power (V²/Hz)", title="Mean PSD over all EEG channels")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week1_psd.png", dpi=120)
    plt.close(fig)

    # Figure 2: 10 s of raw traces, frontal (eye) vs central (motor) channels
    show = ["Fp1", "Fp2", "C3", "Cz", "C4"]
    data = raw.copy().filter(1, 40).get_data(picks=show, start=int(30 * raw.info["sfreq"]),
                                             stop=int(40 * raw.info["sfreq"])) * 1e6
    t = np.arange(data.shape[1]) / raw.info["sfreq"] + 30
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, name in enumerate(show):
        ax.plot(t, data[i] - i * 150, lw=0.7)
    ax.set_yticks([-i * 150 for i in range(len(show))], show)
    ax.set(xlabel="Time (s)", title="Raw EEG 30-40 s, band-passed 1-40 Hz (µV, offset per channel)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "week1_traces.png", dpi=120)
    plt.close(fig)

    # ICA on a 1-40 Hz copy (slow drift hurts ICA), looking for eye components
    ica_raw = raw.copy().filter(1, 40)
    ica = ICA(n_components=20, random_state=SEED, max_iter=800)
    ica.fit(ica_raw)
    eog_idx, scores = ica.find_bads_eog(ica_raw, ch_name=EYE_PROXY, verbose=False)
    lines.append(
        f"ICA (20 components, seed {SEED}): components flagged as eye-related via "
        f"{EYE_PROXY} correlation: {sorted(set(eog_idx))}"
    )
    fig = ica.plot_components(show=False)
    fig = fig[0] if isinstance(fig, list) else fig
    fig.savefig(RESULTS_DIR / "week1_ica_components.png", dpi=100)
    plt.close("all")

    text = "\n".join(lines)
    print(text)
    (RESULTS_DIR / "week1_inspect_raw.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
