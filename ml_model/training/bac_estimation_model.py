"""
TensorFlow Lite BAC Estimation Model
Implements sensor fusion algorithm for alcohol detection from PPG, EDA, and temperature sensors
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
import numpy as np
from typing import Tuple, Optional
import os


class BACEstimationModel:
    """
    Neural network model for BAC estimation using sensor fusion
    Architecture: LSTM + Attention for temporal modeling
    """

    def __init__(
        self,
        sequence_length: int = 10,
        n_features: int = 6,
        lstm_units: int = 64,
        dropout_rate: float = 0.3
    ):
        """
        Args:
            sequence_length: Number of time steps in input sequence
            n_features: Number of sensor features (PPG, EDA, Temp, etc.)
            lstm_units: Number of LSTM units
            dropout_rate: Dropout rate for regularization
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.model = None

    def build_model(self) -> Model:
        """
        Build the BAC estimation model architecture

        Architecture:
        1. Input: [batch, sequence_length, n_features]
        2. Bidirectional LSTM for temporal dependencies
        3. Attention mechanism to focus on relevant time steps
        4. Dense layers for BAC regression
        5. Output: BAC value (g/dL)
        """
        # Input layer
        inputs = layers.Input(
            shape=(self.sequence_length, self.n_features),
            name='sensor_input'
        )

        # Bidirectional LSTM for temporal modeling
        lstm_out = layers.Bidirectional(
            layers.LSTM(
                self.lstm_units,
                return_sequences=True,
                name='bidirectional_lstm'
            )
        )(inputs)

        # Dropout for regularization
        lstm_out = layers.Dropout(self.dropout_rate)(lstm_out)

        # Attention mechanism
        attention = layers.Dense(1, activation='tanh')(lstm_out)
        attention = layers.Flatten()(attention)
        attention = layers.Activation('softmax')(attention)
        attention = layers.RepeatVector(self.lstm_units * 2)(attention)
        attention = layers.Permute([2, 1])(attention)

        # Apply attention weights
        attended = layers.Multiply()([lstm_out, attention])
        attended = layers.Lambda(lambda x: tf.reduce_sum(x, axis=1))(attended)

        # Dense layers for regression
        dense = layers.Dense(32, activation='relu', name='dense_1')(attended)
        dense = layers.Dropout(self.dropout_rate)(dense)

        dense = layers.Dense(16, activation='relu', name='dense_2')(dense)

        # Output layer - BAC estimation
        output = layers.Dense(1, activation='linear', name='bac_output')(dense)

        # Build model
        model = Model(inputs=inputs, outputs=output, name='AlcoWatch_BAC_Model')

        return model

    def compile_model(self, learning_rate: float = 0.001):
        """
        Compile the model with optimizer and loss function

        Args:
            learning_rate: Learning rate for Adam optimizer
        """
        if self.model is None:
            self.model = self.build_model()

        # Custom loss function: MSE with penalty for dangerous predictions
        def bac_aware_loss(y_true, y_pred):
            # Base MSE loss
            mse = tf.reduce_mean(tf.square(y_true - y_pred))

            # Penalty for false negatives (predicting low BAC when high)
            # This is critical for safety - we want to avoid missing high BAC
            dangerous_threshold = 0.08  # Legal limit
            false_negative_mask = tf.cast(
                (y_true > dangerous_threshold) & (y_pred < dangerous_threshold),
                tf.float32
            )
            false_negative_penalty = tf.reduce_mean(
                false_negative_mask * tf.square(y_true - y_pred) * 5.0
            )

            return mse + false_negative_penalty

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss=bac_aware_loss,
            metrics=[
                'mae',  # Mean Absolute Error
                'mse',  # Mean Squared Error
                keras.metrics.RootMeanSquaredError(name='rmse')
            ]
        )

        return self.model

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        callbacks: Optional[list] = None
    ):
        """
        Train the BAC estimation model

        Args:
            X_train: Training sensor sequences
            y_train: Training BAC labels
            X_val: Validation sensor sequences
            y_val: Validation BAC labels
            epochs: Number of training epochs
            batch_size: Batch size
            callbacks: List of Keras callbacks
        """
        if self.model is None:
            self.compile_model()

        if callbacks is None:
            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                ),
                keras.callbacks.ModelCheckpoint(
                    'models/bac_model_best.h5',
                    monitor='val_loss',
                    save_best_only=True
                )
            ]

        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        return history

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model performance on test set

        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")

        # Standard metrics
        loss, mae, mse, rmse = self.model.evaluate(X_test, y_test, verbose=0)

        # Additional safety-critical metrics
        y_pred = self.model.predict(X_test, verbose=0).flatten()

        # Classification accuracy at legal limit (0.08 g/dL)
        threshold = 0.08
        y_test_binary = (y_test > threshold).astype(int)
        y_pred_binary = (y_pred > threshold).astype(int)

        accuracy = np.mean(y_test_binary == y_pred_binary)

        # Safety metrics
        true_positives = np.sum((y_test_binary == 1) & (y_pred_binary == 1))
        false_negatives = np.sum((y_test_binary == 1) & (y_pred_binary == 0))
        false_positives = np.sum((y_test_binary == 0) & (y_pred_binary == 1))
        true_negatives = np.sum((y_test_binary == 0) & (y_pred_binary == 0))

        precision = true_positives / (true_positives + false_positives + 1e-10)
        recall = true_positives / (true_positives + false_negatives + 1e-10)
        f1_score = 2 * (precision * recall) / (precision + recall + 1e-10)

        return {
            'loss': loss,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'classification_accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_negatives': int(false_negatives),  # Critical for safety
            'false_positives': int(false_positives)
        }

    def convert_to_tflite(
        self,
        output_path: str = 'models/bac_model.tflite',
        quantize: bool = True
    ):
        """
        Convert trained model to TensorFlow Lite for mobile deployment

        Args:
            output_path: Path to save .tflite file
            quantize: Whether to apply post-training quantization
        """
        if self.model is None:
            raise ValueError("Model must be trained before conversion")

        # Convert to TensorFlow Lite
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)

        if quantize:
            # Post-training quantization for smaller model size and faster inference
            converter.optimizations = [tf.lite.Optimize.DEFAULT]

            # Use dynamic range quantization
            converter.target_spec.supported_types = [tf.float16]

        tflite_model = converter.convert()

        # Save the model
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)

        print(f"TensorFlow Lite model saved to {output_path}")
        print(f"Model size: {len(tflite_model) / 1024:.2f} KB")

        return tflite_model

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict BAC from sensor data

        Args:
            X: Sensor sequences [batch, sequence_length, n_features]

        Returns:
            BAC predictions [batch]
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")

        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()


class ClimateAdaptiveModel:
    """
    Wrapper for BAC model with climate-specific calibration
    Implements the patent's climate-adaptive feature for Central Asia
    """

    def __init__(self, base_model: BACEstimationModel):
        self.base_model = base_model
        self.calibration_params = {
            'Central_Asia': {
                'temp_coefficient': 0.012,
                'humidity_coefficient': 0.008,
                'base_temp': 30.0
            },
            'Europe': {
                'temp_coefficient': 0.010,
                'humidity_coefficient': 0.006,
                'base_temp': 20.0
            },
            'Default': {
                'temp_coefficient': 0.011,
                'humidity_coefficient': 0.007,
                'base_temp': 25.0
            }
        }

    def calibrate_prediction(
        self,
        bac_raw: float,
        ambient_temp: float,
        humidity: float,
        region: str = 'Default'
    ) -> float:
        """
        Apply climate-specific calibration to raw BAC prediction

        Args:
            bac_raw: Raw BAC prediction from model
            ambient_temp: Ambient temperature (Celsius)
            humidity: Relative humidity (%)
            region: Climate region

        Returns:
            Calibrated BAC value
        """
        params = self.calibration_params.get(region, self.calibration_params['Default'])

        # Temperature adjustment
        temp_diff = ambient_temp - params['base_temp']
        temp_adjustment = temp_diff * params['temp_coefficient']

        # Humidity adjustment
        humidity_adjustment = (humidity - 50) * params['humidity_coefficient'] / 100

        # Apply calibration
        bac_calibrated = bac_raw + temp_adjustment + humidity_adjustment

        # Ensure non-negative
        bac_calibrated = max(0, bac_calibrated)

        return bac_calibrated


# Example usage and training script
if __name__ == "__main__":
    # This would be run as a training script
    print("BAC Estimation Model - Training Script")
    print("=" * 50)

    # Initialize model
    model = BACEstimationModel(
        sequence_length=10,
        n_features=6,
        lstm_units=64,
        dropout_rate=0.3
    )

    # Build and compile
    model.compile_model(learning_rate=0.001)

    print("\nModel Architecture:")
    model.model.summary()

    print("\nModel ready for training!")
    print("Use dataset_loader.py to prepare data, then call model.train()")
