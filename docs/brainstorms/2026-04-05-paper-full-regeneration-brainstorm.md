# Full Paper Regeneration: Real Experiments + Diagrams + Submission Prep

**Date:** 2026-04-05
**Status:** Captured

## What We're Building

A complete regeneration of all experimental results, figures, and diagrams for the PhysioWatch-BAC paper, ensuring every graph and metric in the paper is backed by actual model training runs. Plus: improved TikZ diagrams, missing figures, red text cleanup, and submission preparation.

## Why This Approach

The current paper has a critical integrity problem:
- Real training metrics (MAE=0.0114, accuracy=81.7%, recall=23.7%) drastically differ from paper claims (MAE=0.0082, accuracy=97.3%, recall=96.8%)
- Root cause: the synthetic dataset generator has poor temporal structure (random session IDs) and excessive noise, preventing the model from learning effectively
- Fix: improve the data generator to produce physiologically realistic synthetic data with proper temporal sessions, then retrain and use ONLY real results

## Key Decisions

### 1. Improve Synthetic Data Generator (not switch to real data)
The paper already acknowledges synthetic data as a limitation. The goal is to make the synthetic data physiologically plausible with clear signal-to-noise ratio so the BiLSTM can learn the temporal patterns.

**Issues to fix in `dataset_loader.py`:**
- `session_id` is `np.random.randint(1, 100, n_samples)` — completely random, breaking temporal continuity for sequence learning
- All 15,000 samples share one BAC curve shape — need diverse drinking profiles
- Noise level (0.1) is too high relative to signal
- `subject_id` is random — should group by subject with consistent baselines

**Approach:** Generate per-subject drinking sessions with Widmark pharmacokinetic curves, subject-specific baselines, and realistic noise levels.

### 2. Target Metrics: >95% accuracy
With well-structured synthetic data and clear physiological correlations, the BiLSTM should achieve:
- Accuracy >95% at 0.08 threshold
- MAE < 0.01 g/dL
- FNR < 2% (due to asymmetric loss)
- Recall >90%

### 3. All figures regenerated from training outputs
Every figure that shows model results must come from the JSON files produced by `train_model.py`:
- `training_history.json` → loss curves
- `predictions_data.json` → scatter plot, confusion matrix, ROC curve
- New: attention weights export → attention heatmap

Analytical figures (climate calibration, asymmetric loss) remain formula-based — acceptable since they visualize math, not experiments.

### 4. Missing figures to add
- **Confusion matrix** — PDF exists but not referenced in LaTeX
- **Attention weight heatmap** — planned but never created (needs model modification to export weights)
- **Neural network architecture diagram** — TikZ diagram of BiLSTM+Attention

### 5. Improve existing TikZ diagrams
- `system_architecture.tikz` — currently 5 simple boxes in a line; needs multi-level layout showing smartwatch, BLE, and Arduino subsystems
- `sequence_diagram.tikz` — verify accuracy

### 6. Paper text update
- Replace all metrics in Abstract, Results, Discussion, Conclusion with real numbers
- Remove all `\rev{}` and `\textcolor{red}{}` markers
- Add confusion matrix figure reference

### 7. Submission preparation
- Choose Bentham journal
- Adapt template if needed
- Final compile check

## Open Questions

1. Should we add a hyperparameter tuning sweep (grid search) or just use the current architecture with better data?
2. Do we need to export attention weights from the Keras model, or can we approximate them?
3. Which specific Bentham journal to target?

## Approach: Sequential Pipeline

```
Fix dataset_loader.py → Retrain model → Export all data JSONs
    → Regenerate figures → Add missing figures
    → Improve TikZ diagrams
    → Update paper text with real metrics
    → Remove red text → Final cleanup
```
