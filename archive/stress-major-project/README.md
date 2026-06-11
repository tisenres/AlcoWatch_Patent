# Archive — Stress Detection "Major Project" (frozen)

**Status:** Frozen snapshot. Not maintained. Archived 2026-06-12.

This folder is the **Stress Detection "Major Project"** — a WESAD-based BiLSTM + attention
stress classifier and its surrounding deliverables. It was developed in this repository
alongside the AlcoWatch alcohol patent and the NTCC paper, and is preserved here as a
read-only snapshot after the repository was reorganized to contain only the alcohol patent
on `main`. None of this is part of the alcohol patent.

## Contents

- `stress_detection/` — the Python project (data loaders, feature engineering, training, TFLite export). WESAD raw data and trained model outputs are intentionally **not** included (external dataset / regenerable).
- `tests/stress_detection/` — the project's test suite.
- `wear_os/` — the Wear OS stress integration: `stress/` activity + inference + level enum, `StressBLECharacteristic.kt`, and `STRESS_MODEL_README.txt`.
- `arduino/stress_cabin_control/` — adaptive cabin-control firmware for stress levels.
- `paper_figures/stress/` — generated figures (confusion matrix, architecture, system overview, training history, BLE/FSM diagrams).
- `scripts/` — figure/diagram/deck generation scripts.
- `major-project-report/` — the Major Project Report LaTeX sources (chapters, figures, `main.tex`, `references.bib`).
- `Anastasiia_Major_Project_Defense.pptx` — defense presentation deck.
- `major_project_overleaf.zip`, `Anastasiia_Major_Project.zip` — Overleaf exports.

## History

Full commit history of how this work was built is preserved at the git tag
`archive/stress-ntcc-snapshot` (tip of the former `feat/stress-recognition` branch).
This folder additionally preserves the **untracked** export artifacts that the tag
does not cover.
