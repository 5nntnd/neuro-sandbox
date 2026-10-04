"""Week 1: interactive raw EEG browser for spotting blinks, muscle bursts and bad channels.

Run (from the repo root, with the virtual environment active):
    python experiments/week1_browse_raw.py 9 5 2

Opens a window on the first subject; the others are one key away. Data is average-referenced
and band-passed 1-55 Hz (reference and filter choices as in reference/hypothesis.md, but
wider so muscle stays visible and 60 Hz mains is cut). Nothing here is used for classification.

Channel selection: the checkbox panel on the left lists all 64 channels from front (Fp) to back
(O, Iz), left to right within each row. Tick any channels to show only those, for example just
Fp1 or Fp2. The buttons above it set All / None / Eye+edge / Motor in one click.

Mouse and keys (hover over the plot):
    wheel            scroll time by 1 s          shift+wheel   scroll time by 10 s
    ctrl+wheel       zoom amplitude              left/right    scroll time by 5 s
    n / p            next / previous subject
    b m d x          note a blink / muscle burst / drift / bad channel at the cursor time
    u                undo the last note

Notes are saved to outputs/week1_notes_s<subject>.csv (gitignored scratch folder).
Cue periods are shaded: blue = rest (T0), green = left (T1), orange = right (T2).
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np
from matplotlib.widgets import Button, CheckButtons
from mne.datasets import eegbci

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
RUNS = [4, 8, 12]
# T1/T2 mean left/right fist ONLY in imagery runs 4, 8, 12. See reference/datasets.md before changing RUNS.
assert set(RUNS) <= {4, 8, 12}, "RUNS must be imagery left/right runs 4, 8, 12 (T1=left, T2=right)"
N_EXPLORATORY = 10  # subjects above this are the confirmatory set, see reference/hypothesis.md

PRESETS = {
    "Eye+edge": ["Fp1", "Fpz", "Fp2", "AF7", "AF8", "F7", "F8", "FT7", "FT8", "T7", "T8"],
    "Motor": ["FC3", "FCz", "FC4", "C3", "Cz", "C4", "CP3", "CPz", "CP4"],
}
ROW_ORDER = ["Fp", "AF", "F", "FT", "FC", "T", "C", "TP", "CP", "P", "PO", "O", "I"]  # front to back
N_COLUMNS = 4
CUE_STYLE = {"T0": ("tab:blue", "rest"), "T1": ("tab:green", "left"), "T2": ("tab:orange", "right")}
NOTE_KEYS = {"b": "blink", "m": "muscle", "d": "drift", "x": "bad_channel"}
NOTE_COLORS = {"blink": "tab:red", "muscle": "tab:purple", "drift": "tab:brown", "bad_channel": "tab:pink"}

mne.set_log_level("ERROR")
for _k in list(plt.rcParams):  # free letter and arrow keys from matplotlib's default shortcuts
    if _k.startswith("keymap.") and _k not in ("keymap.quit", "keymap.fullscreen"):
        plt.rcParams[_k] = []


def anterior_posterior_order(names):
    """Sort channel names front to back, and left to right within a row (odd, midline z, even)."""
    def key(name):
        stem = re.sub(r"\d+$", "", name.rstrip("z")) if name.endswith("z") else re.sub(r"\d+$", "", name)
        digits = re.findall(r"\d+$", name)
        x = 0 if name.endswith("z") or not digits else (-int(digits[0]) if int(digits[0]) % 2 else int(digits[0]))
        return ROW_ORDER.index(stem), x
    return sorted(names, key=key)


def load_subject(subject, lo=1.0, hi=55.0):
    DATA_DIR.mkdir(exist_ok=True)
    paths = eegbci.load_data(subject, RUNS, path=str(DATA_DIR), update_path=False)
    raw = mne.concatenate_raws([mne.io.read_raw_edf(p, preload=True) for p in paths])
    eegbci.standardize(raw)
    raw.set_montage("standard_1005")
    raw.set_eeg_reference("average", projection=False)
    raw.filter(lo, hi)
    data = raw.get_data(picks="eeg") * 1e6  # microvolts
    cues = [c for c in zip(raw.annotations.onset, raw.annotations.duration, raw.annotations.description)
            if c[2] in CUE_STYLE]  # drops run-boundary marks
    return raw.ch_names, data, raw.times, cues, raw.info["sfreq"]


class Browser:
    def __init__(self, subjects, window=10.0):
        self.subjects, self.window = subjects, window
        self.idx, self.t0, self.spacing = 0, 0.0, 100.0
        self.notes, self.cursor_t = [], None
        self.selected, self._bulk, self.checks = set(), False, []
        self.fig = plt.figure(figsize=(14, 7.5))
        self.ax = self.fig.add_axes([0.30, 0.08, 0.69, 0.85])
        c = self.fig.canvas
        c.mpl_connect("scroll_event", self.on_scroll)
        c.mpl_connect("key_press_event", self.on_key)
        c.mpl_connect("motion_notify_event", self.on_move)
        self.load()

    # ---- data and notes ----
    @property
    def subject(self):
        return self.subjects[self.idx]

    def load(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, f"Loading subject {self.subject}...", ha="center", transform=self.ax.transAxes)
        self.fig.canvas.draw()
        self.names, self.data, self.times, self.cues, self.sfreq = load_subject(self.subject)
        self.sorted_names = anterior_posterior_order(self.names)
        if not self.checks:
            self.build_panel()
            self.set_selection(PRESETS["Eye+edge"])
        self.t0 = 0.0
        self.notes = self.read_notes()
        self.draw()

    def read_notes(self):
        path = OUT_DIR / f"week1_notes_s{self.subject}.csv"
        if not path.exists():
            return []
        with open(path, newline="") as f:  # older files call the last column "group"
            return [(float(r["time_s"]), r["label"], r.get("channels") or r.get("group", "")) for r in csv.DictReader(f)]

    def save_notes(self):
        OUT_DIR.mkdir(exist_ok=True)
        with open(OUT_DIR / f"week1_notes_s{self.subject}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time_s", "label", "channels"])
            w.writerows(self.notes)

    # ---- channel selection panel ----
    def build_panel(self):
        per_col = -(-len(self.sorted_names) // N_COLUMNS)
        col_w = 0.065
        for i in range(N_COLUMNS):
            names = self.sorted_names[i * per_col:(i + 1) * per_col]
            ax = self.fig.add_axes([0.005 + i * col_w, 0.08, col_w - 0.003, 0.74])
            cb = CheckButtons(ax, names, [False] * len(names))
            for lbl in cb.labels:
                lbl.set_fontsize(8)
            cb.on_clicked(self.on_check)
            self.checks.append(cb)
        self.buttons = []
        for i, name in enumerate(["All", "None", *PRESETS]):
            ax = self.fig.add_axes([0.005 + i * col_w, 0.86, col_w - 0.003, 0.05])
            b = Button(ax, name)
            b.label.set_fontsize(8)
            b.on_clicked(lambda _e, n=name: self.preset(n))
            self.buttons.append(b)
        self.fig.text(0.005, 0.93, "Channels (tick to show)", fontsize=9)

    def set_selection(self, names):
        """Tick exactly these channels. Fires the checkbox callbacks, so the redraw is skipped here."""
        names = set(names)
        self._bulk = True
        for cb in self.checks:
            for j, lbl in enumerate(cb.labels):
                if (lbl.get_text() in names) != cb.get_status()[j]:
                    cb.set_active(j)
        self._bulk = False
        self.selected = names

    def preset(self, name):
        names = {"All": self.names, "None": []}.get(name) or PRESETS.get(name, [])
        self.set_selection(names)
        n = len(self.selected)
        self.spacing = 100.0 if n <= 12 else 60.0 if n <= 32 else 30.0  # keep many rows readable
        self.draw()

    def on_check(self, label):
        if self._bulk:
            return
        self.selected ^= {label}
        self.draw()

    # ---- drawing ----
    def draw(self):
        ax = self.ax
        ax.clear()
        t1 = self.t0 + self.window
        s0, s1 = int(self.t0 * self.sfreq), int(t1 * self.sfreq)
        t = self.times[s0:s1]
        shown = [n for n in self.sorted_names if n in self.selected]
        for row, name in enumerate(shown):
            seg = self.data[self.names.index(name), s0:s1]
            ax.plot(t, seg - seg.mean() - row * self.spacing, lw=0.6, color="k")
        ax.set_yticks([-i * self.spacing for i in range(len(shown))])
        ax.set_yticklabels(shown, fontsize=8 if len(shown) <= 32 else 6)
        ax.set_ylim(-(max(len(shown), 1) - 0.3) * self.spacing, 0.9 * self.spacing)
        ax.set_xlim(self.t0, t1)
        if not shown:
            ax.text(0.5, 0.5, "No channels ticked", ha="center", transform=ax.transAxes, color="grey")
        for onset, dur, desc in self.cues:
            if onset + dur < self.t0 or onset > t1:
                continue
            color, label = CUE_STYLE[desc]
            ax.axvspan(onset, onset + dur, color=color, alpha=0.10, lw=0)
            ax.text(max(onset, self.t0) + 0.05, ax.get_ylim()[1], label, va="top", fontsize=8, color=color)
        for nt, label, _ in self.notes:
            if self.t0 <= nt <= t1:
                ax.axvline(nt, color=NOTE_COLORS[label], lw=1.5)
                ax.text(nt, ax.get_ylim()[0], label, rotation=90, va="bottom", fontsize=8, color=NOTE_COLORS[label])
        ax.set_title(
            f"Subject {self.subject} ({self.idx + 1}/{len(self.subjects)})   {self.t0:.0f}-{t1:.0f} s "
            f"of {self.times[-1]:.0f}   {len(shown)} channels   {self.spacing:.0f} uV per row   "
            f"notes: {len(self.notes)}",
            fontsize=9,
        )
        ax.set_xlabel("Time (s)   |   wheel: time, shift+wheel: 10 s, ctrl+wheel: amplitude, "
                      "n/p: subject, b/m/d/x: note at cursor, u: undo", fontsize=8)
        self.fig.canvas.draw_idle()

    def channel_label(self):
        shown = [n for n in self.sorted_names if n in self.selected]
        return "+".join(shown) if len(shown) <= 4 else f"{len(shown)} channels"

    # ---- events ----
    def move(self, dt):
        self.t0 = float(np.clip(self.t0 + dt, 0, self.times[-1] - self.window))
        self.draw()

    def on_move(self, event):
        self.cursor_t = event.xdata if event.inaxes is self.ax else None

    def on_scroll(self, event):
        direction = -1 if event.button == "up" else 1
        key = event.key or ""
        if "ctrl" in key or "control" in key:
            self.spacing = float(np.clip(self.spacing * (0.8 if direction < 0 else 1.25), 5, 2000))
            self.draw()
        else:
            self.move(direction * (10 if "shift" in key else 1))

    def on_key(self, event):
        k = event.key
        if k == "right":
            self.move(5)
        elif k == "left":
            self.move(-5)
        elif k in ("n", "p"):
            self.idx = (self.idx + (1 if k == "n" else -1)) % len(self.subjects)
            self.load()
        elif k in NOTE_KEYS:
            nt = self.cursor_t if self.cursor_t is not None else self.t0 + self.window / 2
            self.notes.append((round(float(nt), 2), NOTE_KEYS[k], self.channel_label()))
            self.save_notes()
            self.draw()
        elif k == "u" and self.notes:
            self.notes.pop()
            self.save_notes()
            self.draw()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("subjects", type=int, nargs="*", default=[9, 5, 2])
    parser.add_argument("--allow-confirmatory", action="store_true")
    args = parser.parse_args()
    if max(args.subjects) > N_EXPLORATORY and not args.allow_confirmatory:
        sys.exit("Subjects above 10 are the confirmatory set; pass --allow-confirmatory to override.")
    Browser(args.subjects)
    plt.show()


if __name__ == "__main__":
    main()
