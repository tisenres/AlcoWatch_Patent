"""
Complete training pipeline for AlcoWatch BAC estimation model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dataset_loader import AlcoholDatasetLoader
from training.bac_estimation_model import BACEstimationModel, ClimateAdaptiveModel
import matplotlib.pyplot as plt
import numpy as np


def plot_training_history(history):
    """Plot training and validation metrics"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Loss
    axes[0, 0].plot(history.history['loss'], label='Train Loss')
    axes[0, 0].plot(history.history['val_loss'], label='Val Loss')
    axes[0, 0].set_title('Model Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # MAE
    axes[0, 1].plot(history.history['mae'], label='Train MAE')
    axes[0, 1].plot(history.history['val_mae'], label='Val MAE')
    axes[0, 1].set_title('Mean Absolute Error')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE')
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # RMSE
    axes[1, 0].plot(history.history['rmse'], label='Train RMSE')
    axes[1, 0].plot(history.history['val_rmse'], label='Val RMSE')
    axes[1, 0].set_title('Root Mean Squared Error')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('RMSE')
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # Learning rate (if recorded)
    if 'lr' in history.history:
        axes[1, 1].plot(history.history['lr'])
        axes[1, 1].set_title('Learning Rate')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('LR')
        axes[1, 1].set_yscale('log')
        axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig('models/training_history.png')
    print("Training history plot saved to models/training_history.png")


def plot_predictions(y_true, y_pred, title="BAC Predictions vs True Values"):
    """Plot predicted vs true BAC values"""
    plt.figure(figsize=(10, 6))

    # Scatter plot
    plt.scatter(y_true, y_pred, alpha=0.5, s=10)

    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')

    # Legal limit reference
    plt.axvline(x=0.08, color='orange', linestyle=':', label='Legal Limit (0.08)')
    plt.axhline(y=0.08, color='orange', linestyle=':')

    plt.xlabel('True BAC (g/dL)')
    plt.ylabel('Predicted BAC (g/dL)')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('models/predictions_plot.png')
    print("Predictions plot saved to models/predictions_plot.png")


def main():
    """Main training pipeline"""
    print("=" * 70)
    print("AlcoWatch BAC Estimation Model - Training Pipeline")
    print("=" * 70)

    # Step 1: Load and prepare data
    print("\n[1/6] Loading and preparing dataset...")
    loader = AlcoholDatasetLoader(data_dir="data/raw")

    # Create synthetic dataset (replace with real data when available)
    df = loader.create_synthetic_dataset(n_samples=15000, noise_level=0.1)
    print(f"   ✓ Created dataset with {len(df)} samples")

    # Preprocess data
    df_processed = loader.preprocess_data(df, normalize=False, remove_outliers=True)
    print(f"   ✓ Preprocessed to {len(df_processed)} samples (outliers removed)")

    # Create sequences
    X, y = loader.create_sequences(df_processed, sequence_length=10)
    print(f"   ✓ Created {len(X)} sequences")

    # Split data
    X_train, X_val, X_test, y_train, y_val, y_test = loader.get_train_test_split(
        X, y, test_size=0.15, val_size=0.15
    )
    print(f"   ✓ Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Step 2: Initialize model
    print("\n[2/6] Initializing BAC estimation model...")
    model = BACEstimationModel(
        sequence_length=10,
        n_features=6,
        lstm_units=64,
        dropout_rate=0.3
    )

    model.compile_model(learning_rate=0.001)
    print("   ✓ Model compiled")

    # Display model architecture
    print("\n   Model Architecture:")
    model.model.summary()

    # Step 3: Train model
    print("\n[3/6] Training model...")
    history = model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=32
    )
    print("   ✓ Training completed")

    # Step 4: Evaluate model
    print("\n[4/6] Evaluating model on test set...")
    metrics = model.evaluate(X_test, y_test)

    print("\n   Test Set Metrics:")
    print(f"   • MAE: {metrics['mae']:.4f} g/dL")
    print(f"   • RMSE: {metrics['rmse']:.4f} g/dL")
    print(f"   • Classification Accuracy (>0.08): {metrics['classification_accuracy']:.2%}")
    print(f"   • Precision: {metrics['precision']:.2%}")
    print(f"   • Recall: {metrics['recall']:.2%}")
    print(f"   • F1 Score: {metrics['f1_score']:.4f}")
    print(f"\n   Safety Analysis:")
    print(f"   • False Negatives (Dangerous): {metrics['false_negatives']}")
    print(f"   • False Positives (Inconvenient): {metrics['false_positives']}")

    # Step 5: Convert to TensorFlow Lite
    print("\n[5/6] Converting to TensorFlow Lite...")
    model.convert_to_tflite(
        output_path='models/bac_model.tflite',
        quantize=True
    )
    print("   ✓ TFLite model saved")

    # Also save full model
    model.model.save('models/bac_model_full.h5')
    print("   ✓ Full model saved to models/bac_model_full.h5")

    # Step 6: Generate visualizations
    print("\n[6/6] Generating visualizations...")
    plot_training_history(history)

    # Make predictions on test set
    y_pred = model.predict(X_test)
    plot_predictions(y_test, y_pred)

    # Test climate-adaptive calibration
    print("\n" + "=" * 70)
    print("Climate-Adaptive Calibration Test")
    print("=" * 70)

    adaptive_model = ClimateAdaptiveModel(model)

    # Test case: High temperature environment (Central Asia)
    raw_bac = 0.06
    ambient_temp = 35.0  # Hot climate
    humidity = 60.0

    bac_central_asia = adaptive_model.calibrate_prediction(
        raw_bac, ambient_temp, humidity, region='Central_Asia'
    )
    bac_europe = adaptive_model.calibrate_prediction(
        raw_bac, ambient_temp, humidity, region='Europe'
    )

    print(f"\nRaw BAC Prediction: {raw_bac:.4f} g/dL")
    print(f"Ambient Temperature: {ambient_temp}°C, Humidity: {humidity}%")
    print(f"Calibrated BAC (Central Asia): {bac_central_asia:.4f} g/dL")
    print(f"Calibrated BAC (Europe): {bac_europe:.4f} g/dL")

    print("\n" + "=" * 70)
    print("Training Pipeline Complete!")
    print("=" * 70)
    print("\nModel files created:")
    print("  • models/bac_model.tflite (for deployment)")
    print("  • models/bac_model_full.h5 (full Keras model)")
    print("  • models/training_history.png")
    print("  • models/predictions_plot.png")
    print("\nNext steps:")
    print("  1. Integrate TFLite model into Wear OS app")
    print("  2. Test on real sensor data")
    print("  3. Fine-tune with user-specific calibration")


if __name__ == "__main__":
    main()
