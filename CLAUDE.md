# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlcoWatch is an AI-based alcohol detection system that combines a Wear OS smartwatch application with Arduino-based vehicle control. The system uses ML-based sensor fusion (PPG, EDA, temperature) to estimate Blood Alcohol Content (BAC) and automatically controls vehicle ignition via BLE communication. This is a patent-pending technology (Indian Patent ACN1408).

**Critical Safety Context:** This is life-safety critical code. False negatives (failing to detect high BAC) are more dangerous than false positives. The system implements fail-safe design where ignition is BLOCKED by default.

## Architecture

The system consists of three main components:

1. **ML Model** (Python/TensorFlow): Bidirectional LSTM + Attention network for BAC estimation
2. **Wear OS App** (Kotlin): Sensor collection, on-device inference, BLE peripheral
3. **Arduino Module** (C++): BLE central, ignition control with relay-based fail-safe

### Data Flow
```
Smartwatch Sensors (PPG/EDA/Temp)
  → TFLite Model (BAC estimation)
  → BLE Peripheral (AES-256 encrypted)
  → Arduino BLE Central
  → Relay Control (ignition enable/disable)
```

## Common Development Commands

### ML Model Training
```bash
# Navigate to ML directory
cd ml_model

# Create virtual environment (if needed)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Train model and generate TFLite
python training/train_model.py

# Output: models/bac_model.tflite (22 KB, optimized for Wear OS)
# Also creates: models/bac_model_best.h5 (full Keras model for reference)
```

### Wear OS Application
```bash
cd wear_os_app

# Build the app (requires Android Studio)
./gradlew build

# Run tests
./gradlew test

# Build debug APK
./gradlew assembleDebug

# Install on connected device
./gradlew installDebug

# IMPORTANT: Copy TFLite model before building
cp ../ml_model/models/bac_model.tflite app/src/main/assets/
```

**Note:** The Wear OS app requires Android Studio with Kotlin plugin and Wear OS SDK. Build configuration is in `build.gradle` (Kotlin 1.9.20, Compose 1.5.4).

### Arduino Firmware
The Arduino code is located at `arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino`. Upload using Arduino IDE with board set to "Arduino Nano 33 BLE" or compatible.

**Required Libraries:**
- ArduinoBLE (install via Arduino Library Manager)

### System Simulation (No Hardware)
```bash
# From project root (RECOMMENDED for testing)
./RUN_SIMULATION.sh

# Or manually:
cd arduino/simulation
python3 run_simulation.py
```

This runs a complete system test including smartwatch simulation, BLE communication, and vehicle control without any hardware.

**Available Test Scenarios:**
1. Sober driver (BAC < 0.05) - should ALLOW
2. Intoxicated driver (BAC > 0.08) - should BLOCK
3. Watch removed - should BLOCK + alert
4. Realistic drinking progression
5. Safety edge cases
6. All scenarios (complete demo)

## Key Architectural Patterns

### ML Model Architecture
- **Input:** Sequences of sensor data `[batch, 10 timesteps, 6 features]`
- **Features:** PPG value, PPG quality, EDA, skin temp, ambient temp, humidity
- **Architecture:** Bidirectional LSTM (64 units) → Attention mechanism → Dense layers
- **Output:** BAC value (g/dL) with custom loss function that penalizes false negatives 5x
- **Target Metrics:** MAE < 0.01 g/dL, Accuracy > 95%, False Negative Rate < 1%

**Location:** `ml_model/training/bac_estimation_model.py` - class `BACEstimationModel`

**Training Details:**
- Custom loss function at line ~110 applies 5x penalty to false negatives
- Early stopping monitors validation MAE
- Model checkpointing saves best model during training
- TFLite conversion uses dynamic range quantization

### Climate-Adaptive Calibration
The system implements region-specific calibration for temperature/humidity (patent claim):
- **Location:** `ml_model/training/bac_estimation_model.py` - class `ClimateAdaptiveModel`
- **Regions:** Central_Asia, Europe, Default (different temp/humidity coefficients)
- **Formula:** `BAC_calibrated = BAC_raw + temp_adjustment + humidity_adjustment`

### BLE Protocol
**Specification:** `shared/protocols/ble_protocol.md`

Key characteristics:
- **Service UUID:** `12345678-1234-5678-1234-56789abcdef0`
- **BAC Status Characteristic:** 20 bytes (timestamp, BAC float, alert level, confidence, flags)
- **Update Frequency:** Every 30 seconds
- **Security:** AES-256-GCM encryption (defined in spec, not fully implemented in current code)
- **Timeout:** 60 seconds - Arduino blocks ignition if no update received

**Smartwatch Implementation:** `wear_os_app/app/src/main/java/com/alcowatch/wearos/ble/BLEPeripheralManager.kt`
**Arduino Implementation:** `arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino`

### Fail-Safe Design
The Arduino module implements critical safety logic:
1. **Default state:** Ignition BLOCKED (relay LOW)
2. **Required for ALLOW:** Active BLE connection + recent BAC update + BAC < 0.08 + watch worn
3. **Timeout behavior:** Connection lost OR 60s without update → AUTO-BLOCK
4. **Tamper detection:** Watch removal (detected via PPG) → immediate block
5. **Emergency override:** 5-second button hold → temporary enable (5 min) + logging

**Location:** `arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino` - function `setIgnitionState()` and main `loop()`

**State Machine:**
- `IGNITION_ALLOWED` - Green LED, relay enabled
- `IGNITION_BLOCKED` - Red LED, relay disabled, buzzer alert
- `WAITING_FOR_DATA` - Blue LED, waiting for first BAC reading
- `CONNECTION_LOST` - Red LED blinking, automatic block
- `OVERRIDE_ACTIVE` - Yellow (Red+Green), temporary manual override

### Wear OS Sensor Collection
- **API:** Health Services API (not deprecated SensorManager)
- **PPG Frequency:** 64 Hz (via `HEART_RATE_BPM` data type)
- **EDA Handling:** Since most devices lack EDA sensors, it's estimated from HRV (Heart Rate Variability)
- **Location:** `wear_os_app/app/src/main/java/com/alcowatch/wearos/data/sensors/SensorManager.kt`

## Important Code Patterns

### TFLite Model Loading (Wear OS)
```kotlin
// Location: wear_os_app/app/src/main/java/com/alcowatch/wearos/ml/BACInferenceEngine.kt
// Load model from assets
val model = Interpreter(loadModelFile("bac_model.tflite"))

// Input: FloatArray of shape [1, 10, 6] (batch, sequence, features)
// Output: FloatArray of shape [1, 1] (BAC value)
```

### BAC Status Packet Parsing (Arduino)
```cpp
// Location: arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino
void parseBACStatus(const uint8_t* data) {
  // Bytes 0-7: Timestamp (64-bit)
  memcpy(&vehicleState.currentBAC.timestamp, data, 8);
  // Bytes 8-11: BAC Value (float, 32-bit)
  memcpy(&vehicleState.currentBAC.bacValue, data + 8, 4);
  // Byte 12: Alert Level (0=SAFE, 1=WARNING, 2=DANGER, 3=CRITICAL)
  vehicleState.currentBAC.alertLevel = data[12];
  // Byte 13: Confidence (0-100%)
  vehicleState.currentBAC.confidence = data[13];
  // Byte 14: Flags (bit 0=worn, bit 2=quality, bit 3=battery)
  vehicleState.currentBAC.watchWorn = (data[14] & 0x01) != 0;
}
```

### Dataset Creation
The current implementation uses synthetic data (real-world data not available):
- **Location:** `ml_model/data/dataset_loader.py` - class `AlcoholDatasetLoader`
- **Synthetic generation:** Physiological correlations modeled (HR increases with BAC, etc.)
- **When deploying:** Replace synthetic data with real sensor recordings for fine-tuning

## Testing

### ML Model Tests
```bash
cd ml_model
# Note: No formal test suite currently exists
# Test by running training and validating metrics
python training/train_model.py
```

### Integration Testing
```bash
# Complete system simulation (RECOMMENDED)
./RUN_SIMULATION.sh

# Or manually:
cd arduino/simulation
python3 run_simulation.py
# Choose scenario:
# 1 = Sober driver (BAC < 0.05) - should ALLOW
# 2 = Intoxicated driver (BAC > 0.08) - should BLOCK
# 3 = Watch removed - should BLOCK + alert
# 6 = All scenarios (complete demo)
```

### Wear OS Unit Tests
```bash
cd wear_os_app
./gradlew test
./gradlew connectedAndroidTest  # Requires connected Wear OS device/emulator
```

## Critical Constraints

### Legal & Safety
- **Legal BAC limit:** 0.08 g/dL (hardcoded in Arduino: `LEGAL_BAC_LIMIT`)
- **Patent status:** Patent pending - this is proprietary research code
- **False negative priority:** The model loss function applies 5x penalty to false negatives (ml_model/training/bac_estimation_model.py)

### Performance Requirements
- **BAC estimation MAE:** Must be ≤ 0.008 g/dL
- **Inference latency:** < 50ms on Wear OS device
- **Model size:** ≤ 22 KB (TFLite quantized)
- **Battery life:** 24h continuous monitoring on smartwatch
- **BLE range:** Minimum 5m reliable connection

### Hardware Constraints
- **TFLite version:** Must match TensorFlow training version (currently 2.15-2.16)
- **Wear OS SDK:** Minimum API level 30 (Android 11)
- **Arduino memory:** Code must fit in ~248KB program space (Nano 33 BLE)

## Project Structure

### Directories
- `ml_model/` - Python ML pipeline (training, TFLite conversion)
  - `data/` - Dataset loader and synthetic data generation
  - `training/` - Model architecture and training pipeline
  - `models/` - Saved models (`.h5` and `.tflite`)
  - `inference/` - Inference utilities (currently unused)
- `wear_os_app/` - Kotlin/Compose Wear OS application
  - `app/src/main/java/com/alcowatch/wearos/` - Main application code
    - `ble/` - BLE peripheral implementation
    - `data/sensors/` - Sensor data collection
    - `ml/` - TFLite inference engine
    - `presentation/` - UI components
  - `app/src/main/assets/` - Where TFLite model must be placed
- `arduino/firmware/` - C++ Arduino firmware (.ino file)
- `arduino/simulation/` - Python BLE simulator (no hardware testing)
  - `ble_simulator.py` - Complete smartwatch emulator
  - `run_simulation.py` - Main simulation runner
- `shared/protocols/` - BLE protocol specification (human-readable)
- `shared/models/` - Common data structures
- `docs/` - Implementation guides (QUICK_START.md has 30-min setup)

### Main Entry Points
- ML training: `ml_model/training/train_model.py` (complete pipeline)
- Wear OS app: `wear_os_app/app/src/main/java/com/alcowatch/wearos/AlcoWatchApplication.kt`
- Arduino: `arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino` (setup/loop)
- Simulation: `arduino/simulation/run_simulation.py`

### Model Files
- Training output: `ml_model/models/bac_model_best.h5` (full Keras model)
- Deployment model: `ml_model/models/bac_model.tflite` (22 KB quantized)
- **Must copy TFLite to:** `wear_os_app/app/src/main/assets/bac_model.tflite` before building app

## Development Workflow

### When modifying the ML model:
1. Edit `ml_model/training/bac_estimation_model.py`
2. Run `python training/train_model.py` to retrain and export TFLite
3. Copy new `bac_model.tflite` to `wear_os_app/app/src/main/assets/`
4. Rebuild and test Wear OS app
5. Test with simulation: `./RUN_SIMULATION.sh`

### When modifying BLE protocol:
1. Update `shared/protocols/ble_protocol.md` specification
2. Update Arduino parsing in `alcowatch_vehicle_control.ino` (see `parseBACStatus()`)
3. Update Wear OS BLE peripheral in `BLEPeripheralManager.kt`
4. Test with `arduino/simulation/run_simulation.py`

### When adding new sensor features:
1. Update input dimension in `BACEstimationModel` (currently n_features=6)
2. Update Wear OS `SensorManager.kt` to collect new sensor
3. Update `CombinedSensorData` struct
4. Retrain model with new feature
5. Update BLE protocol if packet size changes

### When debugging BLE issues:
1. Check BLE protocol spec: `shared/protocols/ble_protocol.md`
2. Arduino serial monitor shows detailed BLE connection logs
3. Wear OS logs can be viewed via `adb logcat`
4. Test individual components with simulation first

## Known Limitations

1. **Synthetic data:** Current model is trained on synthetic data with physiological correlations, not real alcohol sensor data
2. **EDA simulation:** Most Wear OS devices lack EDA sensors, so it's estimated from HRV (not as accurate)
3. **Climate calibration:** Climate-adaptive coefficients are based on research literature, not validated with real deployment
4. **Encryption:** BLE protocol spec defines AES-256, but current implementation uses basic BLE pairing (not fully encrypted packets)
5. **Mobile app:** Companion mobile app is planned but not implemented (would be in `mobile_app/` directory)
6. **Testing:** No formal unit test suite for ML model; testing primarily via simulation

## Quick Integration Guide

The system has three integration documents available:
- `SIMPLE_INTEGRATION.md` - Quickest path to see everything working
- `INTEGRATION_GUIDE.md` - Complete step-by-step integration
- `TESTING_WITHOUT_HARDWARE.md` - No-hardware testing guide

**Fastest way to validate the system works:**
```bash
./RUN_SIMULATION.sh
# Select scenario 2 (Intoxicated driver) to see ignition blocking
```

## Reference Documentation

- **Quick Start:** `docs/QUICK_START.md` - 30-minute setup guide
- **Full Setup:** `docs/IMPLEMENTATION_GUIDE.md` - Complete deployment instructions
- **System Design:** `docs/SYSTEM_SUMMARY.md` - Technical architecture
- **BLE Protocol:** `shared/protocols/ble_protocol.md` - Communication specification
- **Patent Info:** `ACN1408 Prov._Patent_130625.docx` - Patent application (proprietary)
- **Project Report:** `PROJECT_COMPLETION_REPORT.md` - Full project documentation

## Hardware Pin Assignments (Arduino)

When working with Arduino firmware, these are the critical pin assignments:
- Pin 2: Ignition relay (HIGH = allow, LOW = block)
- Pin 3: Red LED (ignition blocked)
- Pin 4: Green LED (ignition allowed)
- Pin 5: Blue LED (connecting/waiting)
- Pin 6: Buzzer (audio alerts)
- Pin 7: Override button (5-second hold)

## Common Issues and Solutions

### Model not found in Wear OS app
- Ensure TFLite model is copied to `wear_os_app/app/src/main/assets/bac_model.tflite`
- Rebuild project after adding model file
- Check file size is ~22KB

### Arduino not connecting to watch
- Verify BLE is enabled on both devices
- Check UUIDs match in both implementations
- Use simulation to test without hardware: `./RUN_SIMULATION.sh`

### Training fails with memory error
- Reduce batch size in `train_model.py`
- Use smaller sequence length (currently 10 timesteps)
- Check available system RAM

### BLE timeout issues
- Default timeout is 60 seconds (configurable in Arduino firmware)
- Ensure watch is sending updates every 30 seconds
- Check BLE signal strength (minimum 5m range)
