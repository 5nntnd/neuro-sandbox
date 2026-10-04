# Datasets

License and citation notes for each dataset used. Check here before committing anything derived from a dataset.

## PhysioNet EEG Motor Movement/Imagery (EEGMMIDB)

- **Source:** https://physionet.org/content/eegmmidb/1.0.0/ (DOI 10.13026/C28G6P), checked 2026-10-04.
- **License:** Open Data Commons Attribution License v1.0, so reuse is allowed with attribution.
- **Cite:** Schalk (2009) for the dataset; Schalk et al. (2004), "BCI2000: A General-Purpose Brain-Computer Interface (BCI) System", IEEE Trans. Biomed. Eng.; and the PhysioNet platform paper the page lists.
- **Reference and ground electrodes: not documented.** Checked 2026-10-04 in the PhysioNet pages, the BCI2000 wiki and the full text of Schalk et al. (2004); none names them (notes in `reference-check-PCI2000.txt` and `reference-check-Schalk2004.txt`). The only reference Schalk 2004 states ("vertex referenced to both mastoids") is for a different, slow-cortical-potential system. MOABB's "Reference: mastoid" is secondary metadata with no quoted source, so don't rely on it. No source says the data were re-referenced before distribution.
- **Filters:** the EDF headers list `HP:0Hz LP:0Hz N:0Hz` (no hardware high-pass, low-pass or notch), and a method paper states the recordings used no hardware filters. Mains frequency is not stated; subject 1 shows 60 Hz noise, subject 2 only weakly.
- **In this repo:** raw EDF files stay out of git (size), in the gitignored `data/` folder. Derived metrics and figures in `results/` are fine to commit with this attribution.
