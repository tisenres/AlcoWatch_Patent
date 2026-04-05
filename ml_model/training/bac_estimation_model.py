"""
TensorFlow Lite BAC Estimation Model
Implements sensor fusion with BiLSTM + Attention for alcohol detection
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
import numpy as np
from typing import Tuple, Optional
import os


class TemporalSumLayer(layers.Layer):
    """Sum across temporal axis — TFLite-compatible replacement for Lambda."""
    def call(self, inputs):
        return tf.reduce_sum(inputs, axis=1)

    def get_config(self):
        return super().get_config()


class BACEstimationModel:
    """
    Neural network model for BAC estimation using sensor fusion.
    Architecture: BiLSTM + Attention for temporal modeling.
    """

    def __init__(
        self,
        sequence_length: int = 10,
        n_features: int = 6,
        lstm_units: int = 64,
        dropout_rate: float = 0.3
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.model = None
        self._attention_layer_output = None

    def build_model(self) -> Model:
        """
        Build the BAC estimation model.

        Architecture:
        Input [batch, 10, 6] -> BiLSTM [batch, 10, 128] -> Dropout
        -> Attention [batch, 128] -> Dense(32) -> Dropout -> Dense(16) -> Output [batch, 1]
        """
        inputs = layers.Input(
            shape=(self.sequence_length, self.n_features),
            name='sensor_input'
        )

        # Bidirectional LSTM
        lstm_out = layers.Bidirectional(
            layers.LSTM(
                self.lstm_units,
                return_sequences=True,
                name='bidirectional_lstm'
            )
        )(inputs)
        lstm_out = layers.Dropout(self.dropout_rate)(lstm_out)

        # Attention mechanism
        attention_scores = layers.Dense(1, activation='tanh', name='attention_dense')(lstm_out)
        attention_scores = layers.Flatten(name='attention_flatten')(attention_scores)
        attention_weights = layers.Activation('softmax', name='attention_softmax')(attention_scores)

        # Apply attention: broadcast weights and multiply
        attention_expanded = layers.RepeatVector(self.lstm_units * 2)(attention_weights)
        attention_expanded = layers.Permute([2, 1])(attention_expanded)
        attended = layers.Multiply()([lstm_out, attention_expanded])

        # Sum over timesteps (TFLite-compatible custom layer)
        attended = TemporalSumLayer(name='temporal_sum')(attended)

        # Dense layers
        dense = layers.Dense(32, activation='relu', name='dense_1')(attended)
        dense = layers.Dropout(self.dropout_rate)(dense)
        dense = layers.Dense(16, activation='relu', name='dense_2')(dense)
        output = layers.Dense(1, activation='linear', name='bac_output')(dense)

        model = Model(inputs=inputs, outputs=output, name='AlcoWatch_BAC_Model')
        return model

    def compile_model(self, learning_rate: float = 0.001):
        """Compile the model with BAC-aware asymmetric loss."""
        if self.model is None:
            self.model = self.build_model()

        def bac_aware_loss(y_true, y_pred):
            mse = tf.reduce_mean(tf.square(y_true - y_pred))
            dangerous_threshold = 0.08
            false_negative_mask = tf.cast(
                (y_true > dangerous_threshold) & (y_pred < dangerous_threshold),
                tf.float32
            )
            false_negative_penalty = tf.reduce_mean(
                false_negative_mask * tf.square(y_true - y_pred) * 30.0
            )
            return mse + false_negative_penalty

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss=bac_aware_loss,
            metrics=[
                'mae',
                'mse',
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
        """Train the BAC estimation model."""
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
        """Evaluate model performance on test set with safety-critical metrics."""
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")

        loss, mae, mse, rmse = self.model.evaluate(X_test, y_test, verbose=0)
        y_pred = self.model.predict(X_test, verbose=0).flatten()

        threshold = 0.08
        y_test_binary = (y_test > threshold).astype(int)
        y_pred_binary = (y_pred > threshold).astype(int)

        accuracy = np.mean(y_test_binary == y_pred_binary)

        true_positives = np.sum((y_test_binary == 1) & (y_pred_binary == 1))
        false_negatives = np.sum((y_test_binary == 1) & (y_pred_binary == 0))
        false_positives = np.sum((y_test_binary == 0) & (y_pred_binary == 1))
        true_negatives = np.sum((y_test_binary == 0) & (y_pred_binary == 0))

        precision = true_positives / (true_positives + false_positives + 1e-10)
        recall = true_positives / (true_positives + false_negatives + 1e-10)
        f1_score = 2 * (precision * recall) / (precision + recall + 1e-10)
        fnr = false_negatives / (false_negatives + true_positives + 1e-10)
        fpr = false_positives / (false_positives + true_negatives + 1e-10)

        return {
            'loss': loss,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'classification_accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_negatives': int(false_negatives),
            'false_positives': int(false_positives),
            'true_positives': int(true_positives),
            'true_negatives': int(true_negatives),
            'fnr': fnr,
            'fpr': fpr,
        }

    def extract_attention_weights(self, X: np.ndarray) -> np.ndarray:
        """Extract attention weights from the trained model for visualization."""
        if self.model is None:
            raise ValueError("Model must be trained before extracting attention weights")

        attention_layer = self.model.get_layer('attention_softmax')
        attention_model = Model(
            inputs=self.model.input,
            outputs=attention_layer.output
        )
        weights = attention_model.predict(X, verbose=0)
        return weights  # shape: [n_samples, sequence_length]

    def convert_to_tflite(
        self,
        output_path: str = 'models/bac_model.tflite',
        quantize: bool = True
    ):
        """Convert trained model to TensorFlow Lite."""
        if self.model is None:
            raise ValueError("Model must be trained before conversion")

        # Save to SavedModel format first for TF 2.16 compatibility
        saved_model_dir = output_path.replace('.tflite', '_saved_model')
        self.model.export(saved_model_dir)
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)

        # LSTM requires SELECT_TF_OPS for TensorListReserve
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS,
        ]
        converter._experimental_lower_tensor_list_ops = False
        converter.experimental_enable_resource_variables = True

        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]

        tflite_model = converter.convert()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)

        print(f"TFLite model saved to {output_path}")
        print(f"Model size: {len(tflite_model) / 1024:.2f} KB")
        return tflite_model

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict BAC from sensor sequences."""
        if self.model is None:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X, verbose=0).flatten()


class ClimateAdaptiveModel:
    """Wrapper for BAC model with climate-specific calibration."""

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
        """Apply climate-specific calibration to raw BAC prediction."""
        params = self.calibration_params.get(region, self.calibration_params['Default'])

        temp_diff = ambient_temp - params['base_temp']
        temp_adjustment = temp_diff * params['temp_coefficient']
        humidity_adjustment = (humidity - 50) * params['humidity_coefficient'] / 100

        bac_calibrated = bac_raw + temp_adjustment + humidity_adjustment
        return max(0, bac_calibrated)


if __name__ == "__main__":
    print("BAC Estimation Model - Architecture Check")
    print("=" * 50)

    model = BACEstimationModel(
        sequence_length=10, n_features=6,
        lstm_units=64, dropout_rate=0.3
    )
    model.compile_model(learning_rate=0.001)
    print("\nModel Architecture:")
    model.model.summary()
