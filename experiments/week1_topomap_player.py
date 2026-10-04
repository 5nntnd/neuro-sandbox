"""Week 1: scalp topomap player. Scrub through an EEG recording and watch the head map change.

Run (from the repo root, with the virtual environment active):
    python experiments/week1_topomap_player.py 9 5 2

Shows a top-down head map (nose up, ears at the sides) at the 64 standard electrode positions.
The vertical slider selects the time; the map is recomputed for that time. Data is
average-referenced (as in reference/hypothesis.md) and band-passed with the band you pick.
Nothing here is used for classification.

Controls:
    vertical slider   scrub time (up = later)         wheel   +-0.1 s     shift+wheel   +-1 s
    space             play / pause                    left/right  +-0.1 s (shift: +-1 s)
    n / p             next / previous subject         radio buttons   band and measure
    Names             toggle electrode names          Scale slider    colour range

Measures: "voltage" is the filtered signal at that instant; "RMS" is its amplitude over a
0.5 s window centred there, which makes mu/beta (8-30 Hz) and muscle (30-55 Hz) activity easier
to see. The strip beside the slider shows the cue timeline: blue rest, green left, orange right.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider
from mne.datasets import eegbci

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RUNS = [4, 8, 12]
# T1/T2 mean left/right fist ONLY in imagery runs 4, 8, 12. See reference/datasets.md before changing RUNS.
assert set(RUNS) <= {4, 8, 12}, "RUNS must be imagery left/right runs 4, 8, 12 (T1=left, T2=right)"
N_EXPLORATORY = 10  # subjects above this are the confirmatory set, see reference/hypothesis.md

BANDS = {"1-40 Hz": (1, 40, 40), "8-30 mu/beta": (8, 30, 20), "30-55 muscle": (30, 55, 5)}
MEASURES = ["voltage", "RMS (0.5 s)"]
CUE = {"T0": ("tab:blue", "rest"), "T1": ("tab:green", "left"), "T2": ("tab:orange", "right")}
HALF_WINDOW = 0.25  # s, for the RMS measure
SPHERE_RADIUS = 0.115  # m; head outline big enough that all 64 electrodes (incl. T9/T10, Iz) sit inside it
TICK_S = 0.1  # playback step per timer tick

mne.set_log_level("ERROR")
for _k in list(plt.rcParams):  # free arrow keys and others from matplotlib's default shortcuts
    if _k.startswith("keymap.") and _k not in ("keymap.quit", "keymap.fullscreen"):
        plt.rcParams[_k] = []


def load_raw(subject):
    DATA_DIR.mkdir(exist_ok=True)
    paths = eegbci.load_data(subject, RUNS, path=str(DATA_DIR), update_path=False)
    raw = mne.concatenate_raws([mne.io.read_raw_edf(p, preload=True) for p in paths])
    eegbci.standardize(raw)
    raw.set_montage("standard_1005")
    raw.set_eeg_reference("average", projection=False)
    return raw


class Player:
    def __init__(self, subjects):
        self.subjects, self.idx = subjects, 0
        self.t, self.playing = 0.0, False
        self.band, self.measure, self.show_names = "1-40 Hz", "voltage", False
        self.scale = BANDS[self.band][2]
        self.cache = {}
        self._silent = False

        fig = self.fig = plt.figure(figsize=(10.5, 7.2))
        self.ax = fig.add_axes([0.04, 0.08, 0.62, 0.82])
        self.cax = fig.add_axes([0.67, 0.2, 0.015, 0.55])
        self.ax_strip = fig.add_axes([0.80, 0.12, 0.012, 0.76])
        self.ax_slider = fig.add_axes([0.83, 0.12, 0.03, 0.76])
        self.time_text = fig.text(0.80, 0.95, "", fontsize=13, va="center")
        self.ax_band = fig.add_axes([0.89, 0.62, 0.105, 0.2])
        self.ax_meas = fig.add_axes([0.89, 0.42, 0.105, 0.12])
        self.ax_names = fig.add_axes([0.89, 0.34, 0.105, 0.06])
        self.ax_scale = fig.add_axes([0.89, 0.2, 0.012, 0.12])
        self.ax_play = fig.add_axes([0.89, 0.1, 0.105, 0.06])
        self.ax_band.set_title("Band", fontsize=8)
        self.ax_meas.set_title("Measure", fontsize=8)

        self.band_radio = RadioButtons(self.ax_band, list(BANDS))
        self.meas_radio = RadioButtons(self.ax_meas, MEASURES)
        self.names_check = CheckButtons(self.ax_names, ["Names"], [False])
        self.play_btn = Button(self.ax_play, "Play / pause")
        self.band_radio.on_clicked(self.on_band)
        self.meas_radio.on_clicked(self.on_measure)
        self.names_check.on_clicked(self.on_names)
        self.play_btn.on_clicked(lambda _e: self.toggle_play())
        for lbl in self.band_radio.labels + self.meas_radio.labels:
            lbl.set_fontsize(8)

        self.timer = fig.canvas.new_timer(interval=int(TICK_S * 1000))
        self.timer.add_callback(self.tick)
        c = fig.canvas
        c.mpl_connect("scroll_event", self.on_scroll)
        c.mpl_connect("key_press_event", self.on_key)
        self.load_subject()

    # ---- data ----
    @property
    def subject(self):
        return self.subjects[self.idx]

    def load_subject(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, f"Loading subject {self.subject}...", ha="center", transform=self.ax.transAxes)
        self.fig.canvas.draw()
        self.raw = load_raw(self.subject)
        self.info, self.sfreq = self.raw.info, self.raw.info["sfreq"]
        self.names = self.raw.ch_names
        self.duration = self.raw.times[-1]
        self.cache = {}
        ann = self.raw.annotations
        self.cues = [c for c in zip(ann.onset, ann.duration, ann.description) if c[2] in CUE]  # drops run-boundary marks
        self.t = 0.0
        self._build_slider()
        self.draw()

    def band_data(self):
        if self.band not in self.cache:
            lo, hi, _ = BANDS[self.band]
            self.fig.canvas.draw()
            self.cache[self.band] = self.raw.copy().filter(lo, hi).get_data(picks="eeg") * 1e6  # microvolts
        return self.cache[self.band]

    def values(self):
        data = self.band_data()
        i = int(round(self.t * self.sfreq))
        if self.measure == "voltage":
            return data[:, i]
        h = int(HALF_WINDOW * self.sfreq)
        seg = data[:, max(0, i - h):i + h + 1]
        return np.sqrt((seg ** 2).mean(axis=1))

    # ---- drawing ----
    def _build_slider(self):
        self.ax_slider.clear()
        self.slider = Slider(self.ax_slider, "", 0, self.duration, valinit=0, valstep=1 / self.sfreq,
                             orientation="vertical", valfmt="%.2f s")
        self.slider.valtext.set_visible(False)
        self.slider.label.set_visible(False)
        self.slider.on_changed(self.on_slider)
        s = self.ax_strip
        s.clear()
        for onset, dur, desc in self.cues:
            s.axhspan(onset, onset + dur, color=CUE[desc][0], alpha=0.5, lw=0)
        s.set_ylim(0, self.duration)
        s.set_xticks([])
        s.set_yticks([])
        self.strip_line = s.axhline(0, color="k", lw=1.5)

    def cue_label(self):
        for onset, dur, desc in self.cues:
            if onset <= self.t < onset + dur:
                return CUE[desc][1]
        return "-"

    def draw(self):
        vals = self.values()
        voltage = self.measure == "voltage"
        cmap = "RdBu_r" if voltage else "viridis"
        vlim = (-self.scale, self.scale) if voltage else (0, self.scale)
        ax = self.ax
        ax.clear()
        mne.viz.plot_topomap(vals, self.info, axes=ax, show=False, cmap=cmap, vlim=vlim, contours=6,
                             sensors=True, extrapolate="head", sphere=SPHERE_RADIUS, names=self.names if self.show_names else None,
                             res=48)
        ax.set_title(f"Subject {self.subject} ({self.idx + 1}/{len(self.subjects)})    "
                     f"{self.band}, {self.measure}", fontsize=10)
        self.cax.clear()
        self.fig.colorbar(ScalarMappable(Normalize(*vlim), cmap=cmap), cax=self.cax,
                          label="uV" if voltage else "uV (RMS)")
        self.time_text.set_text(f"t = {self.t:.2f} s   cue: {self.cue_label()}")
        self.strip_line.set_ydata([self.t, self.t])
        self.fig.canvas.draw_idle()

    def _scale_slider(self):
        self.ax_scale.clear()
        self.scale_slider = Slider(self.ax_scale, "", 1, 150, valinit=self.scale, valstep=1,
                                   orientation="vertical")
        self.scale_slider.label.set_visible(False)
        self.ax_scale.set_title("Scale", fontsize=8)
        self.scale_slider.on_changed(self.on_scale)

    # ---- events ----
    def set_time(self, t):
        t = float(np.clip(t, 0, self.duration))
        if self.slider.val != t:
            self.slider.set_val(t)  # triggers on_slider
        else:
            self.draw()

    def on_slider(self, val):
        self.t = float(val)
        self.draw()

    def on_scale(self, val):
        self.scale = float(val)
        self.draw()

    def on_band(self, label):
        self.band = label
        self.scale = BANDS[label][2] if self.measure == "voltage" else BANDS[label][2] / 2
        self._scale_slider()
        self.draw()

    def on_measure(self, label):
        self.measure = label
        self.scale = BANDS[self.band][2] if label == "voltage" else BANDS[self.band][2] / 2
        self._scale_slider()
        self.draw()

    def on_names(self, _label):
        self.show_names = not self.show_names
        self.draw()

    def toggle_play(self):
        self.playing = not self.playing
        (self.timer.start if self.playing else self.timer.stop)()

    def tick(self):
        if self.t >= self.duration:
            self.toggle_play()
            return
        self.set_time(self.t + TICK_S)

    def on_scroll(self, event):
        step = 1.0 if "shift" in (event.key or "") else TICK_S
        self.set_time(self.t + (step if event.button == "up" else -step))

    def on_key(self, event):
        k = event.key or ""
        step = 1.0 if k.startswith("shift+") else TICK_S
        base = k.replace("shift+", "")
        if base == "right":
            self.set_time(self.t + step)
        elif base == "left":
            self.set_time(self.t - step)
        elif base == " ":
            self.toggle_play()
        elif base in ("n", "p"):
            if self.playing:
                self.toggle_play()
            self.idx = (self.idx + (1 if base == "n" else -1)) % len(self.subjects)
            self.load_subject()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("subjects", type=int, nargs="*", default=[9, 5, 2])
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if max(args.subjects) > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    player = Player(args.subjects)
    player._scale_slider()
    player.draw()
    plt.show()


if __name__ == "__main__":
    main()
