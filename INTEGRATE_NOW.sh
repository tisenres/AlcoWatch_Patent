#!/bin/bash

# AlcoWatch Quick Integration Script
# Connects all components together

echo "=========================================="
echo "  AlcoWatch System Integration"
echo "=========================================="
echo ""

PROJECT_ROOT="/Users/tisenres/PycharmProjects/AlcoWatch"
cd "$PROJECT_ROOT"

# Step 1: Check ML Model
echo "Step 1: Checking ML Model..."
if [ -f "ml_model/models/bac_model_best.h5" ]; then
    echo "  ✓ Keras model found"
else
    echo "  ❌ Keras model not found"
    echo "  Run: cd ml_model && python training/train_model.py"
    exit 1
fi

# Check for TFLite model
if [ -f "ml_model/models/bac_model.tflite" ]; then
    echo "  ✓ TFLite model found"
else
    echo "  ⚠️  TFLite model not found"
    echo "  Converting Keras model to TFLite..."

    python3 << 'EOF'
import sys
sys.path.append('ml_model')
from training.bac_estimation_model import BACEstimationModel
import tensorflow as tf

# Load Keras model
model = BACEstimationModel()
model.model = tf.keras.models.load_model('ml_model/models/bac_model_best.h5', compile=False)

# Convert to TFLite
model.convert_to_tflite('ml_model/models/bac_model.tflite', quantize=True)
print("✓ TFLite model created")
EOF

    if [ $? -eq 0 ]; then
        echo "  ✓ TFLite conversion successful"
    else
        echo "  ❌ TFLite conversion failed"
        exit 1
    fi
fi

echo ""

# Step 2: Add TFLite to Wear OS App
echo "Step 2: Adding TFLite model to Wear OS app..."
mkdir -p wear_os_app/app/src/main/assets

if [ -f "ml_model/models/bac_model.tflite" ]; then
    cp ml_model/models/bac_model.tflite wear_os_app/app/src/main/assets/
    echo "  ✓ Model copied to assets"
else
    echo "  ❌ TFLite model not found"
    exit 1
fi

echo ""

# Step 3: Check Wear OS App
echo "Step 3: Checking Wear OS app..."
if [ -f "wear_os_app/app/build.gradle" ]; then
    echo "  ✓ Wear OS app structure OK"
else
    echo "  ❌ Wear OS app not found"
    exit 1
fi

echo ""

# Step 4: Check Arduino Firmware
echo "Step 4: Checking Arduino firmware..."
if [ -f "arduino/firmware/alcowatch_vehicle_control.ino" ]; then
    echo "  ✓ Arduino firmware ready"
else
    echo "  ❌ Arduino firmware not found"
    exit 1
fi

echo ""

# Step 5: Show Integration Options
echo "=========================================="
echo "  Integration Complete!"
echo "=========================================="
echo ""
echo "✅ All components ready:"
echo "  • ML Model: ml_model/models/bac_model.tflite"
echo "  • Wear OS: wear_os_app/ (model added to assets)"
echo "  • Arduino: arduino/firmware/alcowatch_vehicle_control.ino"
echo ""
echo "Choose how to integrate:"
echo ""
echo "Option 1: SOFTWARE SIMULATION (RECOMMENDED)"
echo "  ./RUN_SIMULATION.sh"
echo "  → Test everything without hardware"
echo ""
echo "Option 2: WEAR OS + SIMULATED VEHICLE"
echo "  a) Open Android Studio"
echo "  b) Build → Rebuild Project"
echo "  c) Run → Run 'app'"
echo "  → Watch will show real BAC estimates"
echo ""
echo "Option 3: WEAR OS + REAL ARDUINO"
echo "  a) Upload Arduino firmware (Arduino IDE)"
echo "  b) Run Wear OS app (Android Studio)"
echo "  c) Watch Serial Monitor on Arduino"
echo "  → Full hardware integration"
echo ""
echo "=========================================="
echo ""
echo "Want to test now? Run:"
echo "  ./RUN_SIMULATION.sh"
echo ""
