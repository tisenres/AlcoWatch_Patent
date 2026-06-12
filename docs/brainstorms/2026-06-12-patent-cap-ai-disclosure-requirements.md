---
date: 2026-06-12
topic: patent-cap-ai-disclosure
---

# Patent CAP (ACN1408) — AI Framework, Model Diagram & Drawings Package

## Summary

Prepare the AI-disclosure portion of the **Complete-After-Provisional (CAP)** filing for Indian patent **ACN1408** ("AI-Based Alcohol Level Detection and Vehicle Ignition Prevention System"): a 2D-line AI-framework (pipeline) diagram, a 2D-line ML model-architecture diagram (BiLSTM + Attention), and enablement-level explanatory text — plus a compliance audit and redraw of the existing figures and a single consistent reference-numeral scheme across all drawings and the specification text.

---

## Problem Frame

The provisional for ACN1408 was filed 27-06-2025; the CAP (Complete Specification) is due **27-06-2026**. The patent office requested complete technical disclosure with tables/charts/process-flow diagrams and explicitly restricted drawings to **2D line diagrams only** (Indian Patent Act 1970 / Patent Rules 2003).

Two gaps block a strong filing:
1. **The AI is undisclosed.** In the current drawings the AI/ML core is a black box — Figure 1 labels it only "AI Module (BAC estimation)" with a gears icon. A patent CAP requires enablement-level disclosure: the AI framework (signal → decision pipeline) and the actual model architecture must be drawn and explained so a person skilled in the art could reproduce them.
2. **Existing figures are partly non-compliant.** Figure 1 embeds **photographs** of a smartwatch and an Arduino board — disallowed under the "2D line diagrams only" rule, risking objection. Figure 2 (sequence diagram) is already compliant line-art.

The authoritative technical content already exists in the repo (the trained model and the consolidated paper); it has never been rendered into patent-grade line drawings or disclosure text.

---

## Actors

- A1. **Patent office / examiner** — requires complete technical disclosure and strictly 2D line diagrams; rejects photos/color and under-disclosed inventions.
- A2. **Applicant / inventors (Amity University; Anastasiia Shaposhnikova et al.)** — must submit the CAP before the deadline.
- A3. **Patent agent** — assembles the final Form-2 Complete Specification (claims, legal prose); consumes the AI section + drawings produced here.

---

## Requirements

**AI disclosure (the core ask)**
- R1. Produce a **2D-line AI-framework / process-flow diagram** of the end-to-end pipeline: physiological signal acquisition (PPG, EDA, skin temp, ambient temp, humidity) → preprocessing & 10-timestep windowing → 6-feature vector → BiLSTM+Attention inference → climate-adaptive calibration → BAC estimate → threshold/decision logic (0.08 g/dL) → confidence/alert + encrypted BLE status → Arduino ignition control.
- R2. Produce a **2D-line ML model-architecture diagram** matching the implemented network: Input [10 timesteps × 6 features] → Bidirectional LSTM (64 units → 128) → Dropout → temporal Attention (Dense-tanh score → softmax weights → weighted temporal sum → 128-d context) → Dense(32, ReLU) → Dropout → Dense(16, ReLU) → Dense(1, linear) BAC output. Layers labeled with shapes.
- R3. Write **enablement-level explanatory text** for the Complete Specification covering both diagrams: inputs/features, each layer's role, the safety-prioritized asymmetric loss (false negatives penalized ~30×), climate-adaptive calibration, and on-device TFLite quantized deployment — written in patent style and tied to the reference numerals.

**Figure compliance audit (full package)**
- R4. **Redraw Figure 1** (system architecture) as compliant 2D line-art: replace the smartwatch and Arduino photographs with labeled line-art blocks while preserving the data flow (smartwatch sensors → AI module → encrypted BLE → vehicle controller → ignition relay / OBD-II/ECU).
- R5. **Audit Figure 2** (sequence diagram) and any other figures for 2D-line compliance; relabel only as needed for numeral consistency.
- R6. Add a **2D-line method/flow figure for the vehicle-control safety logic** (the fail-safe ignition state machine: BLOCKED-by-default, ALLOW conditions, connection-loss/timeout/watch-removed → block, override) if it strengthens method enablement.

**Cross-referencing & deliverable form**
- R7. Define **one consistent reference-numeral scheme** spanning every figure and used throughout the specification text (numerals → components), with a lookup table.
- R8. Deliver each figure as a **patent-compliant 2D line-art file** (black-and-white, clean vector + raster export), laid out one-per-sheet with applicant name, sheet number, and figure number, ready to drop into `Drawings_ACN1408.docx`.
- R9. Deliver the AI explanation (R3) as a **drop-in section** for the Form-2 Complete Specification, plus the reference-numeral table (R7), collected in the repo (proposed `patent_cap/`).

---

## Success Criteria

- Every drawing in the package is a **2D line diagram** — no photographs, no color/greyscale shading — meeting the Indian Patent Act 1970 / Patent Rules 2003 constraint the office cited.
- The AI framework and model are disclosed at **enablement level**: a person skilled in the art could reproduce the pipeline and network from the figures + text alone.
- **Reference numerals are consistent** across all figures and the specification text (no orphan or conflicting numerals).
- The diagrams **faithfully match the implemented model** (`ml_model/training/bac_estimation_model.py`) — no invented layers or metrics.
- The package is self-contained and hand-off-ready for the patent agent before **27-06-2026**.

---

## Scope Boundaries

### Deferred for later
- Reusing/adapting these AI diagrams for the journal paper (`overleaf_papers/`) — possible later, not part of this filing.

### Outside this work
- Drafting the full legal Complete Specification (claims, abstract, full prose beyond the AI section) — owned by the patent agent (A3).
- The letter's "Product Composition (% range)" and "Biological Resources" requests — those apply to composition-/biological-based inventions; AlcoWatch is a device/method/AI system with no biological composition, so treated as **not applicable** (see Assumptions; confirm with the agent).

---

## Key Decisions

- **Target = patent CAP (ACN1408), not the journal paper** — drives patent drawing conventions (B/W line art, reference numerals, numbered sheets) over journal figure style.
- **Full drawings package, not just the AI figures** — Figure 1's photographs are non-compliant, so a compliant filing requires auditing/redrawing the whole figure set with a unified numeral scheme.
- **Diagrams must mirror the as-built model** — content is sourced from the actual code and the consolidated paper, not idealized.

---

## Dependencies / Assumptions

- **Content sources (authoritative):** `ml_model/training/bac_estimation_model.py` (exact architecture), `ml_model/` (features, loss, calibration, TFLite), `overleaf_papers/` (existing TikZ/figures for the same system), `CLAUDE.md` (system/BLE/Arduino state machine + pins), `Sudhanshu_papers/ACN1408 Prov._Patent_130625 (1).docx` and `Sudhanshu_papers/Drawings_ACN1408.docx` (provisional text + current figures).
- The **road-network U-Net paper** (ICAN 2025, shared by the user) is a **style/quality reference** for model-architecture presentation, not a deliverable target.
- Patent drawing conventions assumed: black-and-white line art, minimal in-figure text (rely on reference numerals), each figure sheet labeled with applicant/sheet/figure.
- **Assumption (confirm):** composition-% and biological-resource disclosures are N/A for this device/AI invention.

---

## Outstanding Questions

### Deferred to Planning

- [Affects R8][Technical] Rendering toolchain for patent-grade 2D line art (e.g., Graphviz, matplotlib, draw.io, or TikZ→render) given no local LaTeX compiler — pick one that outputs clean B/W vector line diagrams.
- [Affects R7][Technical] The concrete reference-numeral numbering scheme (e.g., 100-series per subsystem) and whether the provisional text already implies any numerals to continue.
- [Affects R9][Technical] Output container: update `Drawings_ACN1408.docx` directly vs. deliver a `patent_cap/` figures folder + insertion guide for the agent.
- [Affects R6][User decision] Whether to include the vehicle-control state-machine figure, or keep the package to system + AI-framework + model + sequence figures only.
