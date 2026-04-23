"""BiLSTM + Attention model for 4-class driver stress classification."""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from typing import Optional


class TemporalSumLayer(layers.Layer):
    """TFLite-compatible sum across timestep axis (replaces Lambda)."""

    def call(self, inputs):
        return tf.reduce_sum(inputs, axis=1)

    def get_config(self):
        return super().get_config()


class StressClassificationModel:
    """
    4-class driver stress classifier.
    Architecture: BiLSTM(64) + Attention → Dense(64) → Dense(32) → Softmax(4)
    Input:  [batch, 30 timesteps, 5 features]  (BVP, EDA, TEMP, ACC, IBI)
    Output: [batch, 4] softmax probabilities
    """

    def __init__(
        self,
        sequence_length: int = 30,
        n_features: int = 5,
        lstm_units: int = 64,
        dropout_rate: float = 0.3,
        n_classes: int = 4,
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.n_classes = n_classes
        self.model: Optional[Model] = None

    def build_model(self) -> Model:
        """Build and return the Keras model; no-op if already built."""
        if self.model is not None:
            return self.model
        inputs = keras.Input(shape=(self.sequence_length, self.n_features))

        x = layers.Bidirectional(
            layers.LSTM(self.lstm_units, return_sequences=True)
        )(inputs)
        x = layers.Dropout(self.dropout_rate)(x)

        # Attention mechanism
        attn = layers.Dense(1, activation='tanh')(x)
        attn = layers.Flatten()(attn)
        attn = layers.Activation('softmax')(attn)
        attn = layers.RepeatVector(self.lstm_units * 2)(attn)
        attn = layers.Permute([2, 1])(attn)
        x = layers.Multiply()([x, attn])
        x = TemporalSumLayer()(x)

        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(self.dropout_rate)(x)
        x = layers.Dense(32, activation='relu')(x)
        outputs = layers.Dense(self.n_classes, activation='softmax')(x)

        self.model = Model(inputs=inputs, outputs=outputs, name='stress_classifier')
        return self.model

    def compile(self, learning_rate: float = 0.001) -> None:
        """Compile the model with Adam + categorical cross-entropy; builds if needed."""
        if self.model is None:
            self.build_model()
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy'],
        )
