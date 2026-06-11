---
title: "feat: Full Regeneration of PhysioWatch-BAC Paper Results, Figures, and Diagrams"
type: feat
date: 2026-04-06
---

# Full Regeneration of PhysioWatch-BAC Paper Results, Figures, and Diagrams

## Overview

Every metric, figure, and diagram in the PhysioWatch-BAC paper must be backed by reproducible experiments. Currently, the paper claims metrics (97.3% accuracy, 0.0082 MAE) that drastically differ from actual training output (81.7% accuracy, 0.0114 MAE). This plan covers: fixing the synthetic data generator, retraining the model, regenerating all figures from real outputs, adding missing figures, improving TikZ diagrams, and updating the paper text with actual metrics.

## Problem Statement / Motivation

**Integrity gap:** The paper's hardcoded metrics do not match `ml_model/models/evaluation_metrics.json`. Root causes:
1. `dataset_loader.py` assigns `session_id` randomly (line 129), breaking temporal continuity for sequence learning
2. Normalization is disabled (`normalize=False`, `train_model.py:102`) despite the paper claiming z-score normalization
3. Single BAC curve shape for all 15,000 samples — no diversity
4. Noise level (0.1) is too high relative to signal strength

**Missing content:** Confusion matrix PDF exists but isn't referenced in LaTeX. Attention weight heatmap was planned but never implemented. System architecture TikZ is oversimplified (5 boxes in a line).

## Proposed Solution

Fix the data pipeline → retrain → regenerate everything → update paper with real numbers.

**Target metrics (achievable with clean synthetic data):** >95% accuracy, MAE < 0.01 g/dL, FNR < 2%, Recall > 90%.

---

## Technical Approach

### Phase 1: Fix Training Pipeline

#### 1.1 Rewrite Synthetic Data Generator

**File:** `ml_model/data/dataset_loader.py`

Replace `create_synthetic_dataset()` with structured per-subject drinking sessions:

**Changes:**
- Generate 50 subjects with consistent physiological baselines (body weight 55-95 kg, gender-specific water ratio)
- Each subject has 3-6 drinking sessions with Widmark pharmacokinetic BAC curves
- 3 drinking profiles: light (peak ~0.04), moderate (peak ~0.08-0.10), heavy (peak ~0.15+)
- Widmark formula: `BAC(t) = (A / (r * W)) - (β * t)` where A=alcohol consumed, r=body water ratio, W=weight, β=elimination rate (0.010-0.025 g/dL/hr, normally distributed around 0.015)
- Session IDs are sequential per subject (not random)
- Reduce `noise_level` default from 0.1 to 0.05
- Keep physiological correlations: PPG↑ with BAC (r≈0.82), EDA↑ (r≈0.75), skin temp↑ (r≈0.71), PPG quality↓ (r≈-0.68)
- Total: ~15,000 samples across all subjects/sessions

**Acceptance criteria:**
- [ ] Each subject has a unique baseline (HR, EDA, temp)
- [ ] Sessions are temporally continuous (timestamps sequential within session)
- [ ] BAC profiles follow Widmark curves with per-subject parameters
- [ ] `create_sequences()` groups by session_id produce sequences with >10 samples each
- [ ] Feature-BAC correlations match paper Table 3

#### 1.2 Enable Normalization + Deterministic Training

**File:** `ml_model/training/train_model.py`

- [ ] Change line 102: `normalize=False` → `normalize=True`
- [ ] Add TF deterministic seeding at top of `main()`:
  ```python
  import os
  os.environ['PYTHONHASHSEED'] = '0'
  os.environ['TF_DETERMINISTIC_OPS'] = '1'
  tf.random.set_seed(42)
  np.random.seed(42)
  ```
- [ ] Serialize scaler parameters to `models/scaler_params.json` (mean, std per feature) for deployment
- [ ] Fix `preprocess_data()` to only normalize the 6 model input features (not engineered features that are unused)

#### 1.3 Add TFLite Evaluation

**File:** `ml_model/training/train_model.py`

The paper reports separate Keras vs TFLite metrics (Table 7). Currently only Keras model is evaluated.

- [ ] After TFLite conversion, load the `.tflite` file and run inference on test set
- [ ] Compute TFLite-specific MAE, RMSE, accuracy
- [ ] Save to `models/tflite_evaluation_metrics.json`
- [ ] Update Table 7 values with real Keras vs TFLite comparison

#### 1.4 Add Ablation Baselines

The paper compares BiLSTM+Attention vs LSTM-only (MAE 0.0121) vs SMA (MAE 0.0187). These baselines need real runs.

- [ ] Add LSTM-only baseline (remove attention mechanism) — train and evaluate
- [ ] Add simple moving average baseline — compute on test set
- [ ] Save baseline metrics to `models/ablation_metrics.json`
- [ ] Calculate actual improvement percentages

#### 1.5 Add Attention Weight Export

**File:** `ml_model/training/bac_estimation_model.py`

Build a separate extraction model post-training that shares weights:

- [ ] After training, create `attention_model = Model(inputs=model.input, outputs=attention_softmax_layer)` using the existing attention softmax activation output
- [ ] Extract attention weights for test set samples
- [ ] Save to `models/attention_weights.json` (array of shape [n_test, 10] for 10 timesteps)
- [ ] Select representative samples: 1 sober, 1 near-threshold, 1 intoxicated, 1 during absorption peak

#### 1.6 Fix Lambda Layer for TFLite

**File:** `ml_model/training/bac_estimation_model.py`

Line 78: `layers.Lambda(lambda x: tf.reduce_sum(x, axis=1))` may break TFLite conversion.

- [ ] Replace Lambda with a custom `tf.keras.layers.Layer` subclass or use `tf.keras.backend.sum`
- [ ] Verify TFLite conversion succeeds after change
- [ ] If conversion still fails, note in paper and keep try/except

---

### Phase 2: Run Training + Generate Data

#### 2.1 Full Training Run

```bash
cd ml_model
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python training/train_model.py
```

**Expected outputs in `ml_model/models/`:**
- [ ] `training_history.json` — per-epoch metrics
- [ ] `evaluation_metrics.json` — test set metrics
- [ ] `predictions_data.json` — y_true, y_pred arrays
- [ ] `attention_weights.json` — attention weight arrays + representative samples
- [ ] `ablation_metrics.json` — baseline comparison metrics
- [ ] `scaler_params.json` — normalization parameters
- [ ] `tflite_evaluation_metrics.json` — TFLite-specific metrics
- [ ] `bac_model.tflite` — quantized model
- [ ] `bac_model_best.h5` — best checkpoint

#### 2.2 Validate Metrics Meet Targets

After training, check:
- [ ] Classification accuracy > 95%
- [ ] MAE < 0.01 g/dL
- [ ] FNR < 2%
- [ ] Recall > 90%
- [ ] TFLite model ≤ 22 KB

**If targets not met:** Iterate on hyperparameters (learning rate, LSTM units, dropout, noise level, asymmetric loss multiplier). Maximum 3 iterations before accepting best result.

---

### Phase 3: Regenerate All Figures

#### 3.1 Update Figure Generation Script

**File:** `scripts/generate_paper_figures.py`

- [ ] Add `fig_attention_heatmap()` function: visualize attention weights across 10 timesteps for 3-4 representative samples (sober, near-threshold, intoxicated, absorption peak)
- [ ] Add `--output-dir` default pointing to `Wiley_New_Journal_Design_version_5__NJD_v5___5_/` to eliminate manual copy step
- [ ] Consume new `attention_weights.json` file

#### 3.2 Run Figure Generation

```bash
python scripts/generate_paper_figures.py \
  --data-dir ml_model/models \
  --output-dir Wiley_New_Journal_Design_version_5__NJD_v5___5_/
```

**Expected outputs (all PDF + PNG at 600 DPI):**
- [ ] `loss_curves.pdf` — from training_history.json (real data)
- [ ] `prediction_scatter.pdf` — from predictions_data.json (real data)
- [ ] `confusion_matrix.pdf` — from predictions_data.json (real data)
- [ ] `roc_curve.pdf` — from predictions_data.json (real data)
- [ ] `attention_heatmap.pdf` — from attention_weights.json (NEW, real data)
- [ ] `climate_calibration.pdf` — analytical (formula-based, acceptable)
- [ ] `asymmetric_loss.pdf` — analytical (formula-based, acceptable)

---

### Phase 4: Improve TikZ Diagrams

Can run in parallel with Phases 1-3.

#### 4.1 Redesign System Architecture Diagram

**File:** `Wiley_New_Journal_Design_version_5__NJD_v5___5_/system_architecture.tikz`

Current: 5 boxes in a horizontal line (too simple for a journal paper).

Replace with multi-layer diagram showing:
- **Sensor layer:** PPG, EDA (estimated), Temperature as separate inputs
- **Processing layer:** Feature extraction → BiLSTM+Attention → BAC estimate → Climate calibration
- **Communication layer:** BLE GATT service, 20-byte packet, AES-256
- **Vehicle layer:** Arduino FSM → Relay control → LED/Buzzer feedback
- Dashed boxes grouping "Wear OS Smartwatch" and "Arduino Nano 33 BLE"

- [ ] Rewrite `system_architecture.tikz` with multi-layer layout
- [ ] Verify it compiles and fits within `\textwidth`

#### 4.2 Create Neural Network Architecture Diagram (NEW)

**File:** `Wiley_New_Journal_Design_version_5__NJD_v5___5_/nn_architecture.tikz`

Layer-level block diagram matching Table 2:
- Input [10×6] → BiLSTM [10×128] → Dropout → Attention → Dense(32) → Dropout → Dense(16) → Output [1]
- Tensor shapes annotated on arrows
- Attention mechanism shown as a side branch

- [ ] Create `nn_architecture.tikz`
- [ ] Add `\input{nn_architecture.tikz}` to paper in Methodology section (after Table 2)
- [ ] Write caption and label

#### 4.3 Verify Sequence Diagram

**File:** `Wiley_New_Journal_Design_version_5__NJD_v5___5_/sequence_diagram.tikz`

- [ ] Review for accuracy against current BLE protocol spec
- [ ] Minor improvements if needed

---

### Phase 5: Update Paper Text

#### 5.1 Comprehensive Metric Inventory

All hardcoded values to update after training (locations in `wileyNJDv5_AMA.tex`):

**Abstract (line ~52-56):**
- MAE, classification accuracy, FNR, latency, model size, inference time

**Table 4 — ML Model Performance (lines ~440-452):**
- MAE, RMSE, Accuracy, Precision, Recall, F1, FNR, FPR (target + achieved columns)

**Table 7 — TFLite Optimization (lines ~278-286):**
- Keras model size/precision/inference/memory/MAE vs TFLite values

**Inline Results text (line ~454):**
- MAE, FN/FP percentages, attention weight ratio, LSTM baseline MAE (0.0121), SMA baseline MAE (0.0187), improvement percentages (32%, 56%)

**Quantization section (line ~288):**
- MAE degradation (0.0003), percentage (3.8%), size ratio (54x)

**Table 6 — Training Hyperparameters (lines ~306-308):**
- Sample counts (may change if dataset structure changes)

**Climate section (line ~546):**
- Calibration error values (keep as analytical — not data-dependent)

**Conclusions (line ~556):**
- Repeated MAE, FNR, model size, latency

**Comparison table in Related Work (line ~162):**
- 580ms, 22KB

- [ ] Create a checklist of every value + its line number
- [ ] After training, search-and-replace each with actual value from JSON outputs
- [ ] Double-check abstract, tables, inline text, and conclusions are all consistent

#### 5.2 Remove Red Text Markers

- [ ] Remove all `\rev{...}` wrappers (keep inner text)
- [ ] Remove all `\textcolor{red}{...}` wrappers (keep inner text)
- [ ] Remove `\textcolor{red}{[NEW]}` markers from figure captions entirely (both marker and wrapper)
- [ ] Remove `{\color{red}...}` blocks around Related Work section (keep text)
- [ ] Remove the `\newcommand{\rev}[1]{\textcolor{red}{#1}}` definition (line 25)
- [ ] Verify no red/rev remnants remain

#### 5.3 Add Missing Figure References

- [ ] Add `\includegraphics` + caption + label for confusion matrix (`fig:confusion`)
- [ ] Add `\includegraphics` + caption + label for attention heatmap (`fig:attention`)
- [ ] Add `\input{}` + caption + label for NN architecture diagram (`fig:nn_arch`)
- [ ] Add inline references (`Figure~\ref{fig:confusion}`, etc.) in Results section text
- [ ] Write descriptive text referencing confusion matrix and attention heatmap

#### 5.4 Update Sample Counts

If the new dataset structure changes total samples/sequences:
- [ ] Update Table 6 (Training/Validation/Test sample counts)
- [ ] Update inline text referencing "15,000 samples" or "2,250 test sequences"

---

### Phase 6: Final Cleanup

#### 6.1 Compilation Check

- [ ] Compile LaTeX locally or on Overleaf
- [ ] Verify all figures render correctly
- [ ] Verify all cross-references (`\ref{}`, `\cite{}`) resolve
- [ ] Check no overfull/underfull box warnings on figures
- [ ] Verify bibliography compiles (all cited keys exist in .bib)

#### 6.2 Consistency Audit

- [ ] Every metric in abstract matches Results tables
- [ ] Every metric in Conclusions matches Results tables
- [ ] Comparison table (Table 1) "Ours" column matches actual results
- [ ] No leftover `\rev{}` or `\textcolor{red}` markers
- [ ] Figure count matches total referenced in text

#### 6.3 Generate Updated DIFF File

- [ ] Re-run latexdiff between original and updated version
- [ ] Save as `wileyNJDv5_AMA_DIFF.tex`

---

## Acceptance Criteria

### Functional Requirements
- [ ] All model metrics in paper match `evaluation_metrics.json` exactly
- [ ] All figures generated from JSON data produced by `train_model.py`
- [ ] Confusion matrix included in paper with `\includegraphics`
- [ ] Attention heatmap figure included in paper
- [ ] Neural network architecture TikZ diagram in paper
- [ ] System architecture diagram is multi-layer (not 5 boxes in line)
- [ ] No `\rev{}` or `\textcolor{red}` markers remain
- [ ] TFLite metrics separately evaluated and reported

### Non-Functional Requirements
- [ ] Training is reproducible (deterministic seeding)
- [ ] Figures are 600 DPI vector PDF
- [ ] LaTeX compiles without errors
- [ ] All `\ref{}` and `\cite{}` resolve

### Quality Gates
- [ ] Metrics validated after training before figure generation
- [ ] Paper compiles after all changes
- [ ] Abstract/Tables/Conclusions metrics are consistent

---

## Dependencies & Prerequisites

1. Python ML environment with TensorFlow 2.15-2.16
2. matplotlib with Times New Roman font (or DejaVu Serif fallback)
3. LaTeX compiler (local or Overleaf) for verification
4. All work in `ml_model/` and `Wiley_New_Journal_Design_version_5__NJD_v5___5_/`

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Model doesn't reach >95% accuracy | High | Iterate hyperparameters (max 3 rounds); accept best result and update paper honestly |
| Lambda layer breaks TFLite conversion | Medium | Replace with custom Layer subclass; keep try/except as fallback |
| Different TF version produces different results | Medium | Pin TF version in requirements.txt; use deterministic ops |
| Normalization breaks deployment story | Low | Export scaler params to JSON; note in paper as deployment requirement |
| Too many hardcoded values missed | Medium | Use grep to find all numeric literals; systematic checklist |

## References & Research

### Internal References
- Brainstorm: `docs/brainstorms/2026-04-05-paper-full-regeneration-brainstorm.md`
- Previous plan: `docs/plans/2026-03-25-feat-paper-revision-bentham-science-plan.md`
- Training pipeline: `ml_model/training/train_model.py`
- Model architecture: `ml_model/training/bac_estimation_model.py:40-92`
- Dataset loader: `ml_model/data/dataset_loader.py:47-132`
- Figure generator: `scripts/generate_paper_figures.py`
- Paper source: `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJDv5_AMA.tex`
- System TikZ: `Wiley_New_Journal_Design_version_5__NJD_v5___5_/system_architecture.tikz`

### Key Findings from SpecFlow Analysis
- `normalize=False` is likely the single biggest contributor to poor metrics
- Random `session_id` breaks temporal continuity, causing most data to be discarded in sequence creation
- Lambda layer (line 78 of model) may need replacement for TFLite compatibility
- ~30+ hardcoded metric values across the paper need updating
- Attention export requires a secondary model with shared weights (not architecture change before training)
- Climate calibration and asymmetric loss figures are formula-based (acceptable, no data dependency)
