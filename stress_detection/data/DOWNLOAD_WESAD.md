# WESAD Dataset Download Instructions

The original sciebo link is no longer active. Use one of the three options below.

---

## Option A — Official authors' page (recommended, ~2.5 GB zip)

1. Go to: https://ubi29.informatik.uni-siegen.de/usi/data_wesad.html
2. Click the download link for the ICMI'18 dataset
3. Extract the archive
4. Place the extracted data in: `stress_detection/data/WESAD/`

---

## Option B — UCI ML Repository (programmatic)

```bash
pip install ucimlrepo
python3 - <<'EOF'
from ucimlrepo import fetch_ucirepo
wesad = fetch_ucirepo(id=465)
# Follow UCI instructions to save the raw .pkl files
EOF
```

Note: UCI may only provide pre-extracted features, not raw `.pkl` files.
The training pipeline requires raw `.pkl` files — use Option A or C if UCI returns CSVs only.

---

## Option C — Kaggle

1. Install Kaggle CLI: `pip install kaggle`
2. Set up `~/.kaggle/kaggle.json` with your API token
3. Run:
```bash
kaggle datasets download -d orvile/wesad-wearable-stress-affect-detection-dataset
unzip wesad-wearable-stress-affect-detection-dataset.zip -d stress_detection/data/WESAD/
```

---

## Expected structure after extraction

```
stress_detection/data/WESAD/
├── S2/S2.pkl
├── S3/S3.pkl
├── S4/S4.pkl
...
└── S17/S17.pkl
```

Note: S1 was a pilot study and is excluded. S12 was not collected by the dataset authors
and is absent from the archive — this is expected. The archive contains 15 subjects total
(S2–S11, S13–S17).

---

## After downloading — run training

```bash
cd /path/to/AlcoWatch
source stress_detection/venv/bin/activate   # or your venv
python -m stress_detection.training.train_stress_model
```

Then regenerate paper figures with real metrics:
```bash
python3 scripts/generate_stress_figures.py
```
