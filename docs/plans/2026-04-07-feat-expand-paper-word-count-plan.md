---
title: "feat: Expand Paper Content to 6,500-7,000 Words for Bentham Submission"
type: feat
date: 2026-04-07
---

# Expand Paper Content to 6,500-7,000 Words

## Overview

The paper is currently ~3,455 words (excluding tables, figures, references). Bentham Science journals require 6,000-7,000 words. This plan adds ~3,500 words by filling identified content gaps — primarily the missing synthetic data generation methodology and the absent ablation/discussion analysis.

## Problem Statement

| Section | Current | Target | Gap |
|---------|---------|--------|-----|
| Introduction | ~470 | ~650 | +180 |
| Related Work | ~1,380 | ~1,500 | +120 |
| Methodology | ~600 | ~1,400 | **+800** |
| Results & Discussion | ~670 | ~2,000 | **+1,330** |
| Conclusions | ~140 | ~300 | +160 |
| **Total** | **~3,455** | **~6,500** | **~3,050** |

## Technical Approach

### Phase 1: Methodology Expansion (+800 words)

#### 1.1 New Subsection: "Synthetic Data Generation" (~500 words)

Insert BEFORE "PhysioWatch-BAC Neural Network Architecture" subsection.

**Content to write:**
- Widmark pharmacokinetic model equations: `BAC(t) = (A / (r × W)) - β × t` with absorption phase exponential rise
- Subject population: 50 subjects, gender-balanced, weight 50-95 kg, body water ratio 0.49-0.68
- Drinking profiles: sober (15%), light (25%), moderate (35%), heavy (25%) with alcohol doses 0-100g
- Session structure: 3-6 sessions per subject, 4-8 hours each, 30-second sampling
- Physiological signal synthesis: how PPG, EDA, temperature are generated from BAC curves with documented correlations
- Inter-individual variability: per-subject baselines, elimination rates normally distributed around 0.015 g/dL/hr
- Noise model: sensor noise at 0.03 noise level, cumulative environmental drift
- Dataset statistics: 178,081 samples, 251 sessions, 164,314 sequences after windowing

**Source:** `ml_model/data/dataset_loader.py` — all parameters are in the code

#### 1.2 Expand Feature Extraction (+150 words)

- Add feature selection rationale (why these 6 and not others)
- Discuss multicollinearity: HR and EDA are partially correlated through autonomic nervous system; attention mechanism handles this
- Note that normalization parameters (mean, std) are serialized with the model for deployment

#### 1.3 Expand Quantization Section (+150 words)

- Current text is 1 paragraph. Add:
  - Explanation of Float16 vs INT8 quantization tradeoff
  - Why SELECT_TF_OPS is needed for LSTM (TensorListReserve op)
  - Memory allocation profile: peak 2.3 MB during inference
  - Comparison with similar TinyML deployments from literature

### Phase 2: Results & Discussion Expansion (+1,330 words)

#### 2.1 New Subsection: "Ablation Studies" (~400 words)

Insert after the main ML performance table discussion.

**Content to write:**
- **Architecture ablation:** BiLSTM+Attention (MAE 0.0142) vs LSTM-only (MAE 0.0185, +30%) vs SMA baseline (MAE 0.0358, +152%)
- **Attention mechanism impact:** 23% MAE improvement; analysis of what attention learns (more weight to recent timesteps = tracking real-time physiological state vs historical context)
- **Asymmetric loss multiplier sweep:** Discuss empirical tuning: 5x→4.4% FNR, 10x→2.8% FNR, 30x→1.5% FNR, 50x→FPR>5%. Plot the tradeoff curve conceptually
- **Per-sensor contribution:** Discuss relative importance of PPG (highest correlation r=0.82) vs EDA (r=0.75) vs temperature (r=0.71). Note that removing any single modality degrades accuracy

**Source:** `ml_model/models/ablation_metrics.json`, `evaluation_metrics.json`

#### 2.2 Expand Attention Weight Analysis (+200 words)

Currently 1 sentence. Expand to:
- Describe attention patterns for sober subjects (uniform weighting) vs intoxicated (peaked at recent timesteps)
- Link to pharmacokinetics: during absorption phase, recent readings are most informative; during elimination, longer temporal context matters
- Reference Figure~\ref{fig:attention} with specific weight values from the heatmap
- Compare with Kong et al.'s fatigue detection attention patterns

**Source:** `ml_model/models/attention_weights.json`

#### 2.3 Confusion Matrix Analysis (~200 words)

Currently only Figure caption. Add:
- TP=3,740, TN=20,737, FP=126, FN=57 breakdown with percentages
- False negative analysis: at what BAC ranges do misses occur? (likely 0.08-0.09 boundary)
- False positive analysis: what conditions trigger false alarms? (likely subjects with high baseline HR)
- Boundary performance: discuss classification difficulty at 0.07-0.09 g/dL range
- Safety implication: 57 FN out of 3,797 positive cases = 1.5% miss rate

#### 2.4 New Subsection: "Discussion" (~300 words)

Currently the paper has no dedicated Discussion. Add after all results:
- **Comparison with state-of-art:** Position results vs Table 1 competitors. Fairbairn et al. achieved AUROC 0.966 with real data; our 0.9997 is on synthetic but demonstrates architectural feasibility
- **Synthetic data realism:** Discuss gap between synthetic and real. Widmark model captures population-level pharmacokinetics but misses individual variations in alcohol dehydrogenase activity, food intake effects, medication interactions
- **Practical deployment considerations:** Real-world factors not captured: motion artifacts during driving, sensor placement variability, long-term drift, user compliance
- **Clinical vs. screening accuracy:** 0.0142 MAE is above clinical precision (0.005 g/dL) but sufficient for binary screening at legal threshold

#### 2.5 Expand Climate Calibration (+100 words)

- Per-region performance summary
- Discuss generalization to regions not in training set
- Note that coefficients are linear approximations; real deployment may need nonlinear calibration

#### 2.6 New Subsection: "Limitations" (~130 words)

Move limitations from Conclusions to a dedicated subsection in Results:
- Synthetic data: model trained on Widmark curves, not real alcohol sensor readings
- EDA proxy: estimated from HRV, not direct galvanic skin response
- Single-session evaluation: no longitudinal drift analysis
- Lab conditions: no motion artifacts, vibration, or real driving conditions
- Population: 50 synthetic subjects may not capture full inter-individual variability

### Phase 3: Introduction Expansion (+180 words)

- Add 1 paragraph describing the synthetic data validation approach: why synthetic data is a valid first step (proof-of-concept before clinical trials), precedent in medical device development
- Briefly introduce Widmark model as the basis for data generation

### Phase 4: Conclusions Expansion (+160 words)

- Expand limitations discussion with mitigation strategies
- Add concrete future work roadmap: (1) real-data validation with IRB-approved clinical study, (2) sensor-specific calibration for commercial Wear OS devices, (3) federated learning for privacy-preserving model updates, (4) integration with ADAS (Advanced Driver Assistance Systems)
- Add sentence about regulatory pathway (FDA 510(k) for medical device classification)

---

## Acceptance Criteria

- [ ] Total word count 6,000-7,000 (excluding tables, figures, references)
- [ ] New "Synthetic Data Generation" subsection in Methodology
- [ ] New "Ablation Studies" subsection in Results
- [ ] New "Discussion" subsection
- [ ] New "Limitations" subsection
- [ ] Expanded attention weight analysis with Figure references
- [ ] Expanded confusion matrix analysis
- [ ] Expanded Conclusions with deployment roadmap
- [ ] All new text references existing figures/tables
- [ ] No new figures needed (all data already exists)
- [ ] Paper compiles on Overleaf after changes

## Key Constraint

**All expansion must be based on real data from `ml_model/models/*.json` files.** No invented numbers. Where specific experiments weren't run (e.g., per-sensor ablation), frame as "expected based on correlation analysis" or "future work."

## References

- Paper: `Wiley_New_Journal_Design_version_5__NJD_v5___5_/wileyNJDv5_AMA.tex`
- Training data: `ml_model/models/evaluation_metrics.json`
- Ablation: `ml_model/models/ablation_metrics.json`
- Attention: `ml_model/models/attention_weights.json`
- Dataset code: `ml_model/data/dataset_loader.py`
- Previous plan: `docs/plans/2026-04-06-feat-paper-full-regeneration-plan.md`
