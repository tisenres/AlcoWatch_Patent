# Provisional ↔ As-Built Reconciliation — ACN1408

**For the patent agent.** This note lists points where the **as-built embodiment** (the
AlcoWatch code: `ml_model/`, `wear_os_app/`, `arduino/`, and `CLAUDE.md`) differs from, or
is narrower than, statements in the **provisional specification** (`ACN1408 Prov._Patent_130625`).
A Complete Specification that mirrors the code may otherwise internally contradict its own
provisional or claim subject matter the embodiment does not support — an enablement /
best-mode risk an examiner or opponent can exploit. For each item, decide whether to (a)
keep the code-faithful framing used in `disclosure_ai_section.md`, or (b) amend the
provisional/claim language. **This package does not resolve these — it surfaces them.**

| # | Provisional says | As-built embodiment | Recommended framing |
|---|---|---|---|
| 1 | A smartwatch with an **EDA sensor** "for quantifying sympathetic nervous system responses" | No dedicated EDA sensor; EDA is **estimated/derived from heart-rate variability** (most Wear OS devices lack EDA hardware) | Describe EDA (114) as *estimated/derived*; if claims require a literal EDA sensor, narrow or mark as an optional alternative embodiment |
| 2 | AI infers **"transdermal alcohol concentrations"** which are converted to BAC | No transdermal alcohol sensor; BAC is **regressed from physiological proxies** (PPG/EDA/temperature) by the model | Describe BAC as *inferred from physiological proxies*; avoid asserting transdermal sensing as implemented |
| 3 | Models "**trained on large-scale physiological datasets**" | Trained on **physiologically-modeled synthetic data** in the present embodiment | State the synthetic-data basis honestly (best mode); large-scale real datasets may be claimed as a further embodiment |
| 4 | AI that "**dynamically adjusts / personalizes BAC thresholds** to individual baselines" | Fixed legal threshold of **0.08 g/dL**; region (not individual) calibration coefficients | Either disclose the fixed-threshold embodiment, or keep dynamic/personalized thresholds as a claimed alternative not asserted as built |
| 5 | Provisional Figure 1 (and AI module) depicts **"Security and Biometric Authentication"** | No biometric-authentication function in the model/code | Omit biometric authentication from the redrawn Figure 1 (done) unless it is added to the embodiment; do not claim it as implemented |
| 6 | Communication uses **AES-256 encryption** | AES-256 is **specified** but the current implementation uses basic BLE pairing | Label the link (140) "secure ... AES-256 per spec" (done); disclose AES-256 as the specified/target security, not as the as-shipped implementation |

## Items confirmed consistent (no action)

- **Model architecture** (FIG. 4) matches the code exactly: BiLSTM(64) → [B,10,128],
  Dropout(0.3), temporal attention (Dense-tanh → softmax → weighted sum), Dense 32/16/1.
- **Asymmetric loss** penalizing false negatives **30×** (code: `* 30.0`).
- **Climate-adaptive calibration** is a real post-inference correction (code:
  `ClimateAdaptiveModel.calibrate_prediction`; on-device `applyClimateCalibration`).
- **Fail-safe default-BLOCK** ignition logic (FIG. 5) matches the firmware state machine.
- **0.08 g/dL** legal threshold matches the hardcoded `LEGAL_BAC_LIMIT`.
