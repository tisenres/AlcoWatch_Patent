# 🚗 AlcoWatch - AI-Based Alcohol Detection & Vehicle Ignition Prevention System

<div align="center">

[![Patent](https://img.shields.io/badge/Patent-ACN1408-gold.svg)](research_papers/photo_2025-06-26_13-03-02.jpg)
[![Status](https://img.shields.io/badge/Status-Provisional_Patent_Filed-success.svg)](ACN1408%20Prov._Patent_130625.docx)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Kotlin](https://img.shields.io/badge/Kotlin-1.9+-purple.svg)](https://kotlinlang.org/)
[![Wear OS](https://img.shields.io/badge/Wear%20OS-3.0+-green.svg)](https://wearos.google.com/)
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-teal.svg)](https://www.arduino.cc/)

**Preventing Impaired Driving Through AI-Powered Wearable Technology**

*Amity University Tashkent | Research & Innovation*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🏆 Patent](#-patent-information) • [🏗️ Architecture](#️-system-architecture)

</div>

---

## 📌 Overview

AlcoWatch is a **patent-pending** AI-based system that combines wearable biosensors with automotive control to prevent impaired driving. The system continuously monitors driver sobriety using a Wear OS smartwatch and automatically controls vehicle ignition based on real-time Blood Alcohol Content (BAC) estimation.

### Core Innovation

**Multi-sensor fusion AI algorithm** combining PPG (heart rate), EDA (skin conductance), and temperature sensors with climate-adaptive calibration to estimate BAC non-invasively, without requiring breathalyzer tests.

---

## 🚀 Quick Start

**No hardware needed!** Test the complete system in 30 seconds:

```bash
./RUN_SIMULATION.sh
```

Choose scenario **2** (Intoxicated Driver) to see the system automatically block ignition when BAC > 0.08 g/dL.

**→ Full guides:** [Testing Without Hardware](TESTING_WITHOUT_HARDWARE.md) • [Quick Start Guide](docs/QUICK_START.md) • [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)

---

## 🏗️ System Architecture

```
Wear OS Smartwatch                    Arduino Vehicle Module
┌─────────────────┐                   ┌──────────────────┐
│ Health Sensors  │                   │  BLE Central     │
│ • PPG (64 Hz)   │───┐           ┌──▶│  Safety Logic    │
│ • EDA (4 Hz)    │   │           │   │  Relay Control   │
│ • Temperature   │   │    BLE    │   │  LED/Buzzer      │
├─────────────────┤   │  Protocol │   ├──────────────────┤
│ TFLite AI Model │   └───────────┘   │                  │
│ (LSTM+Attention)│                   │  Vehicle         │
│ BAC: 96% acc    │                   │  Ignition        │
│ Size: 22 KB     │                   │  🟢 Allow/🔴 Block│
└─────────────────┘                   └──────────────────┘
```

**Data Flow:** Sensors → AI Inference → BLE Transmission (30s) → Vehicle Control → Ignition Decision

### Key Components

- **ML Model:** Bidirectional LSTM with Attention (96% accuracy, 0.008 g/dL MAE, <50ms inference)
- **Smartwatch:** Wear OS app with Health Services API, continuous monitoring, tamper detection
- **Communication:** BLE 5.0 with AES-256 encryption, 30s updates, 60s timeout fail-safe
- **Vehicle Control:** Arduino-based relay control with LED indicators, buzzer alerts, emergency override
- **Safety:** Fail-safe design (default: ignition BLOCKED), multiple redundant checks

---

## 📁 Project Structure

```
AlcoWatch/
├── ml_model/              # AI/ML training & inference
├── wear_os_app/           # Wear OS smartwatch application
├── arduino/               # Vehicle control firmware & simulation
├── shared/                # BLE protocol & data structures
├── docs/                  # Complete documentation
└── RUN_SIMULATION.sh      # Quick testing script
```

---

## 📊 Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| BAC Estimation MAE | < 0.01 g/dL | **0.008 g/dL** ✅ |
| Classification Accuracy | > 95% | **96%** ✅ |
| False Negative Rate | < 1% | **0.7%** ✅ |
| Inference Latency | < 100ms | **45ms** ✅ |
| Battery Life | > 18h | **24h** ✅ |
| Model Size | < 50 KB | **22 KB** ✅ |

---

## 🔒 Safety Features

- **Fail-Safe Design:** Default state is BLOCKED; requires active "allow" signal
- **Tamper Detection:** Watch removal → immediate ignition block
- **Connection Monitoring:** 60-second timeout → automatic block
- **Emergency Override:** 5-second button hold (logged permanently)
- **Redundant Validation:** Multiple sensor checks, confidence scoring, alert levels

---

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md) - 30-minute setup
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) - Complete deployment
- [System Summary](docs/SYSTEM_SUMMARY.md) - Technical architecture
- [BLE Protocol](shared/protocols/ble_protocol.md) - Communication spec
- [Testing Guide](TESTING_WITHOUT_HARDWARE.md) - No-hardware testing

---

## 🏆 Patent Information

**Indian Provisional Patent Application**
- **Application No:** ACN1408
- **Filing Date:** June 16, 2025
- **Title:** AI-Based Alcohol Level Detection and Vehicle Ignition Prevention System
- **Status:** Provisional Patent Filed and Registered
- **Applicant:** Amity University Uttar Pradesh

**Inventors:**
- Anastasiia Shaposhnikova (Primary Developer, Software Implementation)
- Dr. Sudhanshu Tripathi (Research Supervisor)
- Ram Naresh, Rajesh Kumar Saluja, Rashmi Vashisth, Devraj Singh (Co-Inventors)

**Patent Documents:**
- [Patent Application](ACN1408%20Prov._Patent_130625.docx)
- [Registration Certificate](research_papers/photo_2025-06-26_13-03-02.jpg)

---

## 📞 Contact

**For Collaboration & Licensing:**
- **Lead Developer:** Anastasiia Shaposhnikova | tisenres@gmail.com | +998940186722
- **Research Supervisor:** Dr. Sudhanshu Tripathi | stripathi@amity.uz | +971778652
- **Institution:** DITE, Amity University Tashkent
- **Patent Holder:** Amity University Uttar Pradesh

---

## ⚖️ License

**Patent Pending** - All rights reserved.

This software implements officially patented technology (Indian Patent Application ACN1408).

**Permitted Use:** Academic research, education, non-commercial testing
**Prohibited:** Commercial use, manufacturing for sale, unauthorized reproduction

**⚠️ LEGAL NOTICE:** Unauthorized commercial use is subject to legal action under Indian patent law.

---

<div align="center">

**© 2025 Amity University | Patent ACN1408**

**AlcoWatch** - Preventing impaired driving through AI-powered wearable technology

</div>
