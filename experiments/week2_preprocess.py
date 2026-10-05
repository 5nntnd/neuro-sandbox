"""Week 2: the frozen preprocessing order in one function.

    from week2_preprocess import preprocess
    epochs, dropped = preprocess(subject)

Order (reference/hypothesis.md, no step tuned on results): drop channels flagged by the
label-blind 30-55 Hz robust-z rule (computed on the native reference), common average
reference, 8-30 Hz band-pass, epoch 0.5-3.5 s after the cue, no baseline, no rejection.
Returns 45 epochs labelled "left" (T1) and "right" (T2), and the list of dropped channels.

Subjects above 10 are the confirmatory set and are refused unless allow_confirmatory=True.
"""
import sys
from pathlib import Path

import mne

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week1_bad_channels import THRESHOLD, robust_z_from_raw  # noqa: E402
from week1_inspect_raw import load_raw  # noqa: E402

BAND = (8.0, 30.0)
TMIN, TMAX = 0.5, 3.5
N_EXPLORATORY = 10
N_TRIALS = 45

mne.set_log_level("ERROR")


def preprocess(subject, drop_flagged=True, allow_confirmatory=False, window=(TMIN, TMAX)):
    """window is for descriptive plots only (week2_erd_timecourse.py); classification uses the frozen default."""
    if subject > N_EXPLORATORY and not allow_confirmatory:
        raise ValueError("Subjects above 10 are the confirmatory set; pass allow_confirmatory=True.")
    raw = load_raw(subject)

    names, z = robust_z_from_raw(raw)
    dropped = [n for n, v in zip(names, z) if v > THRESHOLD] if drop_flagged else []
    raw.drop_channels(dropped)
    raw.set_eeg_reference("average", projection=False)
    raw.filter(BAND[0], BAND[1], picks="eeg")

    events, event_id = mne.events_from_annotations(raw)  # T0 = rest, T1 = left, T2 = right (runs 4, 8, 12)
    epochs = mne.Epochs(
        raw, events, {"left": event_id["T1"], "right": event_id["T2"]},
        tmin=window[0], tmax=window[1], baseline=None, preload=True,
        reject=None, reject_by_annotation=False,  # no rejection, also none at run-boundary annotations
    )
    assert len(epochs) == N_TRIALS, f"subject {subject}: expected {N_TRIALS} epochs, got {len(epochs)}"
    return epochs, dropped
