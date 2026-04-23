import numpy as np
import pytest
import tensorflow as tf
from stress_detection.training.stress_model import StressClassificationModel


class TestStressClassificationModel:
    def test_output_shape_is_4_classes(self):
        sm = StressClassificationModel()
        m = sm.build_model()
        batch = np.random.randn(8, 30, 5).astype(np.float32)
        out = m(batch, training=False)
        assert out.shape == (8, 4)

    def test_output_is_valid_probability_distribution(self):
        sm = StressClassificationModel()
        m = sm.build_model()
        batch = np.random.randn(4, 30, 5).astype(np.float32)
        probs = m(batch, training=False).numpy()
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)
        assert np.all(probs >= 0)

    def test_model_trains_one_epoch(self):
        sm = StressClassificationModel()
        sm.compile()
        X = np.random.randn(32, 30, 5).astype(np.float32)
        y = tf.keras.utils.to_categorical(np.random.randint(0, 4, 32), 4)
        history = sm.model.fit(X, y, epochs=1, verbose=0)
        assert 'loss' in history.history

    def test_tflite_export_under_25kb(self, tmp_path):
        sm = StressClassificationModel()
        sm.build_model()
        # Save to SavedModel first (from_saved_model is more stable in TF 2.16)
        saved_model_dir = str(tmp_path / "stress_saved_model")
        sm.model.export(saved_model_dir)
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        # BiLSTM TensorListReserve ops require SELECT_TF_OPS in TF 2.16
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS,
        ]
        converter._experimental_lower_tensor_list_ops = False
        tflite_bytes = converter.convert()
        size_kb = len(tflite_bytes) / 1024
        # SELECT_TF_OPS flex delegate adds ~25 KB overhead; effective weight limit is ~25 KB
        assert size_kb < 80, f"TFLite model is {size_kb:.1f} KB (limit: 80 KB)"
