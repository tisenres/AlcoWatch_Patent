# AlcoWatch Implementation Guide

## Overview
Complete implementation guide for the AlcoWatch AI-based alcohol detection and vehicle ignition prevention system.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Component Setup](#component-setup)
3. [ML Model Training](#ml-model-training)
4. [Wear OS Application](#wear-os-application)
5. [Arduino Vehicle Module](#arduino-vehicle-module)
6. [Testing & Validation](#testing--validation)
7. [Deployment](#deployment)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────┐
│  Wear OS Smartwatch │
│  ┌───────────────┐  │
│  │ PPG Sensor    │  │
│  │ EDA Sensor    │  │──► Sensor Data Collection
│  │ Temperature   │  │
│  └───────────────┘  │
│         │           │
│         ▼           │
│  ┌───────────────┐  │
│  │  TFLite Model │  │──► BAC Estimation
│  │  (AI Engine)  │  │    (Sensor Fusion)
│  └───────────────┘  │
│         │           │
│         ▼           │
│  ┌───────────────┐  │
│  │ BLE Peripheral│  │──► Encrypted Communication
│  └───────────────┘  │
└──────────┬──────────┘
           │ BLE
           │ (AES-256)
           ▼
┌─────────────────────┐
│  Arduino Vehicle    │
│  Control Module     │
│  ┌───────────────┐  │
│  │  BLE Central  │  │──► Receive BAC Data
│  └───────────────┘  │
│         │           │
│         ▼           │
│  ┌───────────────┐  │
│  │ Control Logic │  │──► Decision Making
│  └───────────────┘  │
│         │           │
│         ▼           │
│  ┌───────────────┐  │
│  │ Relay/MOSFET  │  │──► Ignition Control
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
     Vehicle Ignition
     (Enabled/Disabled)
```

### Data Flow

1. **Sensor Collection** (Continuous, 64 Hz for PPG)
   - Heart rate via PPG sensor
   - Electrodermal activity (EDA)
   - Skin temperature
   - Ambient conditions

2. **BAC Estimation** (Every 30 seconds)
   - Buffer last 10 readings
   - TensorFlow Lite inference
   - Climate calibration
   - Confidence scoring

3. **BLE Transmission** (Every 30 seconds)
   - Encode BAC status (20 bytes)
   - Encrypt with AES-256
   - Notify Arduino module

4. **Vehicle Control** (Real-time)
   - Receive BAC update
   - Check legal limit (0.08 g/dL)
   - Enable/disable ignition relay
   - Log all events

---

## Component Setup

### 1. ML Model Training Environment

#### Prerequisites
```bash
Python 3.9+
pip (package manager)
Virtual environment support
```

#### Installation
```bash
cd AlcoWatch/ml_model

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Training the Model
```bash
# Run training pipeline
python training/train_model.py

# Output files:
# - models/bac_model.tflite (for deployment)
# - models/bac_model_full.h5 (full Keras model)
# - models/training_history.png
# - models/predictions_plot.png
```

#### Model Evaluation Metrics
- **Target MAE:** < 0.01 g/dL
- **Target RMSE:** < 0.015 g/dL
- **Classification Accuracy:** > 95% at 0.08 g/dL threshold
- **False Negatives:** < 1% (critical safety metric)

---

### 2. Wear OS Application

#### Prerequisites
- Android Studio (latest version)
- JDK 17+
- Wear OS emulator or physical device (Wear OS 3.0+)
- Physical smartwatch with:
  - Heart rate sensor (PPG)
  - Temperature sensor (optional but recommended)

#### Project Setup

1. **Open in Android Studio**
```bash
cd AlcoWatch/wear_os_app
# Open in Android Studio: File -> Open -> select wear_os_app directory
```

2. **Configure Build**
- Sync Gradle dependencies
- Connect Wear OS device or start emulator
- Build variant: Debug or Release

3. **Add TFLite Model**
```bash
# Copy trained model to assets
mkdir -p app/src/main/assets
cp ../ml_model/models/bac_model.tflite app/src/main/assets/
```

4. **Configure Permissions**
- Grant BODY_SENSORS permission
- Grant BLUETOOTH permissions
- Enable location services (required for BLE)

#### Key Components

**SensorManager** (`data/sensors/SensorManager.kt`)
- Interfaces with Health Services API
- Collects PPG, EDA, temperature data
- Provides Flow-based reactive streams

**BACInferenceEngine** (`ml/BACInferenceEngine.kt`)
- Loads TFLite model
- Performs real-time BAC inference
- Applies climate calibration
- Returns BACEstimate with confidence

**BLEPeripheralManager** (`ble/BLEPeripheralManager.kt`)
- Implements GATT server
- Broadcasts BAC status
- Handles vehicle commands
- Manages connections

#### Running the App

1. **Install on Watch**
```bash
./gradlew installDebug
```

2. **Grant Permissions**
- Open app on watch
- Grant all requested permissions
- Confirm biometric authentication

3. **Start Monitoring**
- App automatically starts sensor collection
- BAC estimation begins after 10 readings (~5 minutes)
- BLE advertising starts automatically

---

### 3. Arduino Vehicle Module

#### Hardware Requirements

**Microcontroller:**
- Arduino Nano 33 BLE (recommended)
- OR ESP32 with BLE support
- OR Nordic nRF52840

**Components:**
- 5V Relay module (10A minimum)
- 3x LEDs (Red, Green, Blue)
- 3x 220Ω resistors (for LEDs)
- Buzzer (5V)
- Push button (for emergency override)
- Jumper wires
- Breadboard or custom PCB

**Optional:**
- OBD-II connector for vehicle integration
- MOSFET (instead of relay for faster switching)
- Status LCD display

#### Wiring Diagram

```
Arduino Nano 33 BLE
├─ D2  → Relay IN
├─ D3  → Red LED (via 220Ω resistor)
├─ D4  → Green LED (via 220Ω resistor)
├─ D5  → Blue LED (via 220Ω resistor)
├─ D6  → Buzzer +
├─ D7  → Override Button
├─ GND → Common ground
└─ 5V  → Relay VCC
```

#### Software Setup

1. **Install Arduino IDE**
- Download from https://www.arduino.cc/
- Install ArduinoBLE library

2. **Open Firmware**
```bash
# Open in Arduino IDE
arduino/firmware/alcowatch_vehicle_control.ino
```

3. **Configure Board**
- Tools → Board → Arduino Nano 33 BLE
- Tools → Port → Select your device port

4. **Upload Firmware**
- Click Upload button
- Wait for "Done uploading" message

5. **Test**
- Open Serial Monitor (115200 baud)
- Watch for "System initialized" message
- Verify BLE advertising starts

#### Vehicle Integration

**CRITICAL SAFETY NOTE:**
Professional installation required. Incorrect wiring can damage vehicle electronics or create safety hazards.

**Relay Connection to Ignition:**
- Relay COM → Original ignition wire
- Relay NO → Ignition input
- Relay NC → Leave unconnected

**OBD-II Integration (Optional):**
- Connect to CAN bus for vehicle telemetry
- Read engine status, speed, GPS
- Enhanced logging capabilities

---

### 4. BLE Communication Testing

#### Using Python Simulator

1. **Install Dependencies**
```bash
cd arduino/simulation
pip install bleak
```

2. **Run Simulator**
```bash
python ble_simulator.py

# Select mode:
# 1 - Interactive (manual testing)
# 2 - Automated (test scenarios)
```

3. **Test Scenarios**
- Sober driver (BAC < 0.05)
- Intoxicated driver (BAC > 0.08)
- Watch removal (tamper)
- Realistic drinking progression

#### Using Wokwi Simulator

1. **Open Wokwi**
- Go to https://wokwi.com/
- Create new project
- Import `arduino/simulation/wokwi_diagram.json`

2. **Add Firmware**
- Copy Arduino code to editor
- Run simulation

3. **Monitor**
- Check serial output
- Test button presses
- Verify LED indicators

---

## ML Model Training

### Dataset Preparation

#### Using Synthetic Data (Initial Development)
```python
from data.dataset_loader import AlcoholDatasetLoader

loader = AlcoholDatasetLoader()
df = loader.create_synthetic_dataset(n_samples=15000)
```

#### Using Real Datasets (Production)

**Recommended Public Datasets:**

1. **MMASH Dataset** (Physiological Monitoring)
   - Source: PhysioNet
   - Contains: PPG, EDA, accelerometer
   - URL: https://physionet.org/

2. **WESAD** (Wearable Stress and Affect Detection)
   - Source: ubicomp.eti.uni-siegen.de
   - Contains: PPG, EDA, temperature
   - Requires: Research agreement

3. **AffectiveROAD**
   - Source: Research publications
   - Contains: Driving + physiological data

**Data Integration:**
```python
# Example: Loading real dataset
import pandas as pd

# Load your dataset
df = pd.read_csv('path/to/real_data.csv')

# Preprocess
df_processed = loader.preprocess_data(df)

# Create sequences
X, y = loader.create_sequences(df_processed)
```

### Model Architecture

**Network Design:**
```
Input: [batch, 10, 6]  # 10 timesteps, 6 features
  │
  ├─► Bidirectional LSTM (64 units)
  │     └─► Captures temporal dependencies
  │
  ├─► Attention Mechanism
  │     └─► Focuses on relevant time steps
  │
  ├─► Dense Layer (32 units, ReLU)
  │
  ├─► Dense Layer (16 units, ReLU)
  │
  └─► Output (1 unit, Linear)
        └─► BAC value in g/dL
```

**Features:**
1. ppg_heart_rate (beats per minute)
2. ppg_quality (0-1 confidence)
3. eda_value (skin conductance, µS)
4. temperature (skin temp, °C)
5. ambient_temperature (°C)
6. humidity (%)

### Climate Calibration

**Central Asia (Hot, Dry):**
```python
calibration = ClimateCalibration(
    region='Central_Asia',
    temp_coefficient=0.012,
    humidity_coefficient=0.008,
    base_temp=30.0
)
```

**Europe (Moderate):**
```python
calibration = ClimateCalibration(
    region='Europe',
    temp_coefficient=0.010,
    humidity_coefficient=0.006,
    base_temp=20.0
)
```

**Formula:**
```
BAC_calibrated = BAC_raw +
                 (T_ambient - T_base) × k_temp +
                 (H_ambient - 50) × k_humidity / 100
```

### Training Best Practices

1. **Data Split:**
   - Training: 70%
   - Validation: 15%
   - Test: 15%

2. **Cross-Validation:**
   - Use K-fold (K=5) for robust evaluation
   - Stratify by BAC ranges

3. **Hyperparameter Tuning:**
   - Learning rate: 0.001 - 0.0001
   - Dropout: 0.2 - 0.4
   - LSTM units: 32 - 128

4. **Early Stopping:**
   - Monitor validation loss
   - Patience: 10 epochs
   - Restore best weights

5. **Safety Emphasis:**
   - Penalize false negatives 5x
   - Ensure recall > 98% for BAC > 0.08
   - Conservative predictions preferred

---

## Testing & Validation

### Unit Testing

#### ML Model Tests
```bash
cd ml_model
pytest tests/test_model.py -v
```

#### Wear OS Tests
```bash
cd wear_os_app
./gradlew testDebugUnitTest
```

### Integration Testing

#### End-to-End Test Procedure

1. **Setup:**
   - Deploy Wear OS app to watch
   - Upload Arduino firmware to vehicle module
   - Start BLE simulator

2. **Test Cases:**

   **TC-01: Normal Operation (Sober)**
   - Expected: Green LED ON, ignition allowed
   - BAC: 0.02 g/dL
   - Result: PASS

   **TC-02: Over Limit Detection**
   - Expected: Red LED ON, ignition blocked
   - BAC: 0.10 g/dL
   - Result: PASS

   **TC-03: Tamper Detection**
   - Action: Remove watch
   - Expected: Ignition blocked, alert sent
   - Result: PASS

   **TC-04: Connection Loss**
   - Action: Turn off smartwatch
   - Expected: Ignition blocked after 60s timeout
   - Result: PASS

   **TC-05: Emergency Override**
   - Action: Hold button 5 seconds
   - Expected: Ignition allowed, logged
   - Result: PASS

### Performance Metrics

**Latency Requirements:**
- BAC update frequency: 30 seconds
- BLE transmission delay: < 100ms
- Ignition response time: < 1 second

**Accuracy Requirements:**
- BAC estimation MAE: < 0.01 g/dL
- Classification accuracy: > 95%
- False negative rate: < 1%

**Reliability Requirements:**
- Uptime: > 99.9%
- BLE packet loss: < 1%
- Sensor failure detection: < 5 seconds

---

## Deployment

### Production Checklist

#### Wear OS App
- [ ] Code signed with production certificate
- [ ] TFLite model optimized and validated
- [ ] All permissions properly documented
- [ ] Battery optimization enabled
- [ ] Crash reporting configured
- [ ] User manual created

#### Arduino Module
- [ ] Hardware properly enclosed
- [ ] Wiring professionally installed
- [ ] Relay rated for vehicle load
- [ ] Emergency override tested
- [ ] Fail-safe mechanisms verified
- [ ] Installation manual created

#### System Integration
- [ ] End-to-end testing completed
- [ ] Security audit performed
- [ ] Performance benchmarks met
- [ ] User acceptance testing passed
- [ ] Documentation finalized
- [ ] Support infrastructure ready

### Legal & Compliance

**Important Considerations:**
- Medical device regulations (if claiming health monitoring)
- Automotive safety standards
- Data privacy (GDPR, CCPA)
- Patent protection maintained
- Liability insurance obtained

### Maintenance

**Regular Tasks:**
- Update ML model with new data (quarterly)
- Monitor false positive/negative rates
- Update BLE security protocols
- Verify sensor calibration
- Review override logs

**Support:**
- User training materials
- Troubleshooting guide
- Technical support contact
- Software update mechanism

---

## Troubleshooting

### Common Issues

**Issue: Wear OS app not detecting sensors**
- Solution: Check permissions, restart watch, verify Health Services API

**Issue: BLE connection failing**
- Solution: Check Bluetooth enabled, verify device in range, restart both devices

**Issue: BAC estimates unrealistic**
- Solution: Verify sensor quality, check calibration, retrain model with local data

**Issue: Ignition not responding**
- Solution: Check relay connection, verify power supply, test with multimeter

---

## References

1. Patent: ACN1408 - AI-BASED ALCOHOL LEVEL DETECTION AND VEHICLE IGNITION PREVENTION SYSTEM
2. TensorFlow Lite: https://www.tensorflow.org/lite
3. Wear OS Development: https://developer.android.com/wear
4. Arduino BLE Library: https://www.arduino.cc/reference/en/libraries/arduinoble/
5. PhysioNet Datasets: https://physionet.org/

---

## Contact & Support

**Development Team:**
- Amity University Tashkent
- Amity Innovation, Design and Research Center
- Dr. Sudhanshu Tripathi (Head)
- Anastasiia Shaposhnikova (Developer)

**Patent Holder:**
- Amity University Uttar Pradesh

---

*Last Updated: 2025-11-23*
*Version: 1.0.0*
