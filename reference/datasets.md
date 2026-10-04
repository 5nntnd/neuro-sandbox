# Datasets

License and citation notes for each dataset used. Check here before committing anything derived from a dataset.

## PhysioNet EEG Motor Movement/Imagery (EEGMMIDB)

- **Source:** https://physionet.org/content/eegmmidb/1.0.0/ (DOI 10.13026/C28G6P), checked 2026-10-04.
- **License:** Open Data Commons Attribution License v1.0, so reuse is allowed with attribution.
- **Cite:** Schalk (2009) for the dataset; Schalk et al. (2004), "BCI2000: A General-Purpose Brain-Computer Interface (BCI) System", IEEE Trans. Biomed. Eng.; and the PhysioNet platform paper the page lists.
- **Reference and ground electrodes: not documented.** Checked 2026-10-04 in the PhysioNet pages, the BCI2000 wiki and the full text of Schalk et al. (2004); none names them (notes in `reference-check-PCI2000.txt` and `reference-check-Schalk2004.txt`). The only reference Schalk 2004 states ("vertex referenced to both mastoids") is for a different, slow-cortical-potential system. MOABB's "Reference: mastoid" is secondary metadata with no quoted source, so don't rely on it. No source says the data were re-referenced before distribution.
- **Filters:** the EDF headers list `HP:0Hz LP:0Hz N:0Hz` (no hardware high-pass, low-pass or notch), and a method paper states the recordings used no hardware filters. Mains frequency is not stated; subject 1 shows 60 Hz noise, subject 2 only weakly.
- **In this repo:** raw EDF files stay out of git (size), in the gitignored `data/` folder. Derived metrics and figures in `results/` are fine to commit with this attribution.

### Run numbers and event labels

The PhysioNet page says T1/T2 change meaning between runs and tells users to map codes by run number, but it has no run table. This table is from the MNE documentation for `eegbci.load_data` (checked 2026-10-04):

| Runs | Task | T1 | T2 |
|---|---|---|---|
| 1, 2 | Baseline, eyes open / closed | - | - |
| 3, 7, 11 | Movement: left vs right fist | left fist | right fist |
| **4, 8, 12** | **Imagery: left vs right fist (used here)** | **left fist** | **right fist** |
| 5, 9, 13 | Movement: both fists vs both feet | both fists | both feet |
| 6, 10, 14 | Imagery: both fists vs both feet | both fists | both feet |

T1/T2 map to left/right here only because we load runs 4, 8 and 12. The experiment scripts assert this. Adding runs 6, 10 or 14 (hands vs feet, a possible Week 4 extension) needs a run-aware label mapping first. T0 is rest in every run.
