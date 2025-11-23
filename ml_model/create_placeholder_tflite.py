#!/usr/bin/env python3
"""
Create a minimal placeholder TFLite model for testing
This allows the app to run while the full model is being fixed
"""
import tensorflow as tf
import os
import numpy as np

MODEL_DIR = "models"
TFLITE_MODEL_PATH = os.path.join(MODEL_DIR, "bac_model.tflite")

def create_placeholder_model():
    """Create a simple placeholder model with the expected input/output shape"""
    print("Creating placeholder TFLite model...")

    # Expected input: [batch, 10 timesteps, 6 features]
    # Expected output: [batch, 1] (BAC value)

    # Create a simple sequential model
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(10, 6)),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid', name='bac_output')
    ])

    # Initialize with random weights
    dummy_input = np.random.rand(1, 10, 6).astype(np.float32)
    _ = model.predict(dummy_input, verbose=0)

    print(f"Model created. Input shape: {model.input_shape}")
    print(f"Output shape: {model.output_shape}")

    # Convert to TFLite without optimization (compatibility)
    print("\nConverting to TFLite...")
    # Create a concrete function
    @tf.function(input_signature=[tf.TensorSpec(shape=[None, 10, 6], dtype=tf.float32)])
    def model_func(x):
        return model(x)

    converter = tf.lite.TFLiteConverter.from_concrete_functions([model_func.get_concrete_function()])
    tflite_model = converter.convert()

    # Save the model
    print(f"Saving placeholder TFLite model to {TFLITE_MODEL_PATH}...")
    with open(TFLITE_MODEL_PATH, 'wb') as f:
        f.write(tflite_model)

    # Get file size
    size_kb = len(tflite_model) / 1024
    print(f"\n✓ Placeholder TFLite model created successfully!")
    print(f"  Size: {size_kb:.2f} KB")
    print(f"  Location: {TFLITE_MODEL_PATH}")
    print(f"\n⚠️  NOTE: This is a placeholder model that returns random BAC values.")
    print(f"  For production, the trained model needs to be properly converted.")

    return TFLITE_MODEL_PATH

if __name__ == "__main__":
    create_placeholder_model()
