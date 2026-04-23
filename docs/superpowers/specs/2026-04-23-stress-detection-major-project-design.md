# Design: AI-Based Real-Time Driver Stress Detection and Adaptive Vehicle Environment Control System

**Date:** 2026-04-23
**Type:** Major Project Report — Amity University Tashkent
**Author:** Anastasiia Igorevna Shaposhnikova, A85204923019
**Supervisor:** Dr. Ram Naresh, Professor, Department of IT and Engineering
**Degree:** B.Sc (IT), Semester 6 Section 1, Batch 2023-2026
**Academic Year:** 2025-26
**Deadline:** ~9 months from April 2026

---

## 1. Project Overview

Extension of the AlcoWatch system (Patent ACN1408, Minor Project 2024-25) from alcohol detection to real-time driver stress detection with adaptive vehicle cabin environment control. Both systems share the same hardware platform (Wear OS smartwatch + Arduino + BLE) but operate as independent software modules.

**Title:** "AI-Based Real-Time Driver Stress Detection and Adaptive Vehicle Environment Control System"

---

## 2. Repository Structure

New module added alongside existing `ml_model/`:

```
AlcoWatch/
├── ml_model/                        # existing BAC detection (unchanged)
├── stress_detection/                # NEW module
│   ├── data/
│   │   ├── wesad_loader.py          # WESAD dataset downloader + preprocessor
│   │   └── feature_engineering.py  # BVP/EDA/Temp/ACC/IBI feature extraction
│   ├── training/
│   │   ├── stress_model.py          # BiLSTM+Attention classifier
│   │   └── train_stress_model.py    # training script
│   └── models/                      # saved models, metrics, TFLite
├── wear_os_app/                     # extended with stress module
│   └── app/src/main/java/com/alcowatch/wearos/
│       ├── stress/
│       │   ├── StressInferenceEngine.kt
│       │   └── StressMonitorActivity.kt
│       └── ble/
│           └── StressBLECharacteristic.kt
├── arduino/
│   ├── firmware/                    # existing ignition control (unchanged)
│   └── stress_cabin_control/        # NEW Arduino firmware
│       └── stress_cabin_control.ino
├── research_papers/
│   └── Anastasiia_Major_Project.tex # NEW Major Project Report (LaTeX)
└── scripts/
    └── generate_stress_figures.py   # figures for the paper
```

---

## 3. Data Pipeline

**Dataset:** WESAD (Wearable Stress and Affect Detection) — wrist sensor data from Empatica E4.

**Wrist sensors used (matching Wear OS capabilities):**
- BVP — Blood Volume Pulse (≈ PPG)
- EDA — Electrodermal Activity
- TEMP — Skin Temperature
- ACC — Accelerometer (3-axis → magnitude)
- IBI — Inter-Beat Interval (→ HRV feature)

**Input shape:** `[batch, 30 timesteps, 5 features]`

**Label mapping (WESAD → 4-level driving stress):**

WESAD has 3 conditions: baseline, stress, amusement. We create 4 levels by splitting the stress condition using signal intensity thresholding: stress periods where EDA > 75th percentile AND HRV < 25th percentile are labelled Critical; remaining stress periods are labelled Moderate.

| WESAD Label | Split Rule | Driving Stress Level | Index | Cabin Response |
|---|---|---|---|---|
| Baseline | — | Calm | 0 | Normal lighting, low ventilation, silence |
| Amusement | — | Mild | 1 | Normal lighting, medium ventilation |
| Stress | EDA ≤ 75th pct OR HRV ≥ 25th pct | Moderate | 2 | Blue light, high ventilation, soft music |
| Stress | EDA > 75th pct AND HRV < 25th pct | Critical | 3 | Red blinking, max ventilation, voice alert |

---

## 4. ML Model

**Architecture:** BiLSTM + Attention (adapted from AlcoWatch BAC model)

- Input: `[batch, 30, 5]`
- BiLSTM: 64 units → `[batch, 30, 128]`
- Dropout: 0.3
- Attention: → `[batch, 128]`
- Dense(64, ReLU) → Dropout(0.3) → Dense(32, ReLU) → Dense(4, Softmax)
- Loss: categorical crossentropy
- Output: 4-class probability distribution

**Key difference from AlcoWatch:** regression (→ float BAC) replaced by classification (→ softmax 4 classes). Architecture is otherwise parallel.

**Target metrics:**
- Accuracy > 93%
- F1-score (macro) > 0.90
- False Critical Rate < 2%
- TFLite model size ≤ 25 KB
- Inference latency < 50ms on Wear OS

---

## 5. Wear OS Application

**New components** (parallel to existing BAC components):

- `StressInferenceEngine.kt` — loads stress TFLite model, runs inference every 30s
- `StressMonitorActivity.kt` — displays current stress level with color coding (green/yellow/orange/red)
- `StressBLECharacteristic.kt` — new BLE characteristic (new UUID) transmitting stress level + confidence + timestamp
- `SensorManager.kt` — extended to collect accelerometer as 5th feature

**BLE Stress Packet:** 12 bytes — timestamp (8B) + stress level (1B) + confidence (1B) + flags (2B)

---

## 6. Arduino Cabin Control

**New firmware:** `stress_cabin_control.ino` (independent from ignition control firmware)

**Pin assignments:**
- Pin 2: Red LED (PWM)
- Pin 3: Green LED (PWM)
- Pin 4: Blue LED (PWM)
- Pin 5: Fan/ventilation motor (PWM speed control)
- Pin 6: DFPlayer Mini (audio — TX/RX)
- Pin 7: Override button

**State machine (4 states):**

| State | Lighting | Ventilation | Audio |
|---|---|---|---|
| CALM (0) | Warm white | Low (30%) | Silence |
| MILD (1) | Neutral white | Medium (50%) | — |
| MODERATE (2) | Calm blue | High (75%) | Soft music |
| CRITICAL (3) | Red blinking | Max (100%) | Warning + voice prompt |

**Fail-safe:** if BLE connection lost for >60s → WAITING state, ventilation stays at last level.

---

## 7. Simulation

Extended `RUN_SIMULATION.sh` with new stress scenarios:

| Scenario | Description | Expected Output |
|---|---|---|
| 1 | Relaxed highway driving | CALM → no intervention |
| 2 | Heavy traffic jam | MODERATE → blue light + ventilation |
| 3 | Near-accident panic | CRITICAL → alert + max intervention |
| 4 | Watch removed | CONNECTION_LOST → default state |
| 5 | Gradual fatigue buildup | CALM → MILD → MODERATE progression |

---

## 8. Major Project Report Structure

**Format:** Same as existing NTCC Minor Project Report (LaTeX, Amity University template)
**Estimated length:** 70-80 pages

| Chapter | Title | Key Content |
|---|---|---|
| 1 | Introduction | Driver stress statistics, motivation, problem statement, objectives, scope, link to Patent ACN1408 |
| 2 | Literature Review | Physiological stress markers, WESAD, ML for stress detection, wearable systems, adaptive vehicle environments |
| 3 | System Architecture | Overall architecture, data flow diagram, comparison table with AlcoWatch |
| 4 | Methodology | WESAD preprocessing, BiLSTM+Attention classifier, Wear OS modules, BLE protocol, Arduino FSM |
| 5 | Implementation | Key code listings, TFLite conversion, dataset statistics |
| 6 | Results & Evaluation | Confusion matrix, F1/accuracy, latency analysis, integration tests, SOTA comparison |
| 7 | Conclusion | Summary, limitations, future work (unifying with AlcoWatch into single platform) |

---

## 9. Implementation Phases

1. **Phase 1** — WESAD data pipeline + stress model training (real metrics for paper)
2. **Phase 2** — Arduino stress cabin firmware + simulation scenarios
3. **Phase 3** — Wear OS stress module (Kotlin)
4. **Phase 4** — Paper figures generation (confusion matrix, architecture diagrams, results tables)
5. **Phase 5** — Major Project Report writing (LaTeX, full 70-80 pages)
