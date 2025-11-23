#!/usr/bin/env python3
"""
Convert the existing H5 model to TFLite format
"""
import tensorflow as tf
import os

# Paths
MODEL_DIR = "models"
H5_MODEL_PATH = os.path.join(MODEL_DIR, "bac_model_best.h5")
TFLITE_MODEL_PATH = os.path.join(MODEL_DIR, "bac_model.tflite")

def convert_to_tflite():
    """Convert H5 model to TFLite with quantization"""
    print(f"Loading model from {H5_MODEL_PATH}...")

    # Load the Keras model with unsafe mode (trusted source with Lambda layers)
    model = tf.keras.models.load_model(H5_MODEL_PATH, safe_mode=False)

    print(f"Model loaded. Input shape: {model.input_shape}")
    print(f"Output shape: {model.output_shape}")

    # Convert to TFLite with dynamic range quantization
    print("\nConverting to TFLite with quantization...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    # Save the model
    print(f"Saving TFLite model to {TFLITE_MODEL_PATH}...")
    with open(TFLITE_MODEL_PATH, 'wb') as f:
        f.write(tflite_model)

    # Get file size
    size_kb = len(tflite_model) / 1024
    print(f"\n✓ TFLite model created successfully!")
    print(f"  Size: {size_kb:.2f} KB")
    print(f"  Location: {TFLITE_MODEL_PATH}")

    return TFLITE_MODEL_PATH

if __name__ == "__main__":
    convert_to_tflite()
