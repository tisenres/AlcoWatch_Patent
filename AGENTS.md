# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlcoWatch is an AI-based alcohol detection system combining a Wear OS smartwatch with Arduino-based vehicle control. The system uses ML-based sensor fusion (PPG, EDA, temperature) to estimate Blood Alcohol Content (BAC) and controls vehicle ignition via BLE.

**Critical Safety Context:** This is life-safety critical code. False negatives (failing to detect high BAC) are more dangerous than false positives. The system implements fail-safe design where ignition is BLOCKED by default.

## Architecture

```
Smartwatch Sensors (PPG/EDA/Temp)
  → TFLite Model (BAC estimation)
  → BLE Peripheral (AES-256 encrypted)
  → Arduino BLE Central
  → Relay Control (ignition enable/disable)
```

**Components:**
1. **ML Model** (`ml_model/`): Bidirectional LSTM + Attention network (Python/TensorFlow)
2. **Wear OS App** (`wear_os_app/`): Sensor collection, on-device inference, BLE peripheral (Kotlin)
3. **Arduino Module** (`arduino/firmware/`): BLE central, ignition control with relay-based fail-safe (C++)

## Research Papers

Located in `overleaf_papers/` (LaTeX source files for Overleaf):

| Paper | Purpose | File |
|-------|---------|------|
| **NTCC Paper** | University submission (Amity) - simpler format | `Anastasiia_NTCC.tex` |
| **IEEE Paper** | Journal publication - formal IEEE format | `AlcoWatch_IEEE_Paper.tex` |
| **IEEE Humanized** | IEEE paper with improved readability | `AlcoWatch_IEEE_Paper_Humanized.tex` |

## Common Commands

### ML Model
```bash
cd ml_model
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python training/train_model.py  # Outputs: models/bac_model.tflite (22 KB)
```

### Wear OS App
```bash
cd wear_os_app
cp ../ml_model/models/bac_model.tflite app/src/main/assets/  # Required before build
./gradlew build
./gradlew test
./gradlew installDebug  # Deploy to connected device
```

### System Simulation (No Hardware)
```bash
./RUN_SIMULATION.sh
# Or: cd arduino/simulation && python3 run_simulation.py
```
Scenarios: 1=Sober (ALLOW), 2=Intoxicated (BLOCK), 3=Watch removed (BLOCK), 6=All scenarios

## Key Files

| Purpose | Location |
|---------|----------|
| Model architecture | `ml_model/training/bac_estimation_model.py` |
| Model training | `ml_model/training/train_model.py` |
| Dataset loader | `ml_model/data/dataset_loader.py` |
| Wear OS entry point | `wear_os_app/app/src/main/java/com/alcowatch/wearos/AlcoWatchApplication.kt` |
| BLE peripheral | `wear_os_app/app/src/main/java/com/alcowatch/wearos/ble/BLEPeripheralManager.kt` |
| Sensor collection | `wear_os_app/app/src/main/java/com/alcowatch/wearos/data/sensors/SensorManager.kt` |
| TFLite inference | `wear_os_app/app/src/main/java/com/alcowatch/wearos/ml/BACInferenceEngine.kt` |
| Arduino firmware | `arduino/firmware/alcowatch_vehicle_control/alcowatch_vehicle_control.ino` |
| BLE protocol spec | `shared/protocols/ble_protocol.md` |

## ML Model Details

- **Input:** `[batch, 10 timesteps, 6 features]` (PPG value, PPG quality, EDA, skin temp, ambient temp, humidity)
- **Output:** BAC value (g/dL)
- **Custom loss:** 5x penalty for false negatives (line ~110 in `bac_estimation_model.py`)
- **Target metrics:** MAE < 0.01 g/dL, Accuracy > 95%, False Negative Rate < 1%
- **Climate calibration:** `ClimateAdaptiveModel` class supports region-specific adjustments

## BLE Protocol

- **Service UUID:** `12345678-1234-5678-1234-56789abcdef0`
- **BAC Status:** 20 bytes (timestamp 8B, BAC float 4B, alert level 1B, confidence 1B, flags 1B)
- **Update frequency:** Every 30 seconds
- **Timeout:** 60 seconds → Arduino blocks ignition

## Arduino Safety Logic

**State Machine:**
- `IGNITION_ALLOWED` - Green LED, relay enabled
- `IGNITION_BLOCKED` - Red LED, relay disabled (DEFAULT STATE)
- `WAITING_FOR_DATA` - Blue LED
- `CONNECTION_LOST` - Red LED blinking
- `OVERRIDE_ACTIVE` - Yellow, temporary manual override (5-second hold, 5 min duration, logged)

**Pin Assignments:**
- Pin 2: Ignition relay (HIGH=allow, LOW=block)
- Pin 3: Red LED | Pin 4: Green LED | Pin 5: Blue LED
- Pin 6: Buzzer | Pin 7: Override button

**Required for ALLOW:** Active BLE + recent BAC update + BAC < 0.08 + watch worn

## Development Workflows

**Modifying ML model:**
1. Edit `ml_model/training/bac_estimation_model.py`
2. Run `python training/train_model.py`
3. Copy `bac_model.tflite` to `wear_os_app/app/src/main/assets/`
4. Test with `./RUN_SIMULATION.sh`

**Modifying BLE protocol:**
1. Update `shared/protocols/ble_protocol.md`
2. Update `parseBACStatus()` in Arduino firmware
3. Update `BLEPeripheralManager.kt` in Wear OS app

**Adding sensor features:**
1. Update `n_features` in `BACEstimationModel` (currently 6)
2. Update `SensorManager.kt` to collect new sensor
3. Retrain model

## Critical Constraints

- **Legal BAC limit:** 0.08 g/dL (hardcoded as `LEGAL_BAC_LIMIT`)
- **Model size:** ≤ 22 KB (TFLite quantized)
- **Inference latency:** < 50ms on Wear OS
- **TFLite version:** Must match TensorFlow 2.15-2.16
- **Wear OS SDK:** Minimum API level 30
- **Arduino memory:** ~248KB program space (Nano 33 BLE)

## Known Limitations

1. Model trained on synthetic data (physiological correlations modeled, not real alcohol sensor data)
2. EDA estimated from HRV since most Wear OS devices lack EDA sensors
3. AES-256 encryption defined in spec but uses basic BLE pairing in current implementation
4. No formal ML unit test suite; testing via simulation