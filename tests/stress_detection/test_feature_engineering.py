import numpy as np
import pytest
from stress_detection.data.feature_engineering import (
    resample_to_4hz,
    compute_ibi,
    map_wesad_labels,
    create_windows,
    normalize_features,
)


class TestResample:
    def test_bvp_64hz_to_4hz(self):
        sig = np.random.randn(640).astype(np.float32)  # 10 sec at 64Hz
        out = resample_to_4hz(sig, source_hz=64)
        assert out.shape == (40,)  # 10 sec * 4Hz

    def test_already_4hz_unchanged(self):
        sig = np.random.randn(40).astype(np.float32)
        out = resample_to_4hz(sig, source_hz=4)
        np.testing.assert_array_equal(out, sig)

    def test_acc_32hz_to_4hz(self):
        sig = np.random.randn(320).astype(np.float32)  # 10 sec at 32Hz
        out = resample_to_4hz(sig, source_hz=32)
        assert out.shape == (40,)


class TestComputeIBI:
    def test_output_same_length_as_input(self):
        bvp = np.sin(2 * np.pi * 1.2 * np.linspace(0, 10, 40)).astype(np.float32)
        ibi = compute_ibi(bvp)
        assert ibi.shape == (40,)

    def test_ibi_values_positive(self):
        bvp = np.sin(2 * np.pi * 1.0 * np.linspace(0, 10, 40)).astype(np.float32)
        ibi = compute_ibi(bvp)
        assert np.all(ibi > 0)


class TestMapWesadLabels:
    def test_baseline_maps_to_calm(self):
        labels = np.array([1] * 700, dtype=np.int32)  # 1 second baseline at 700Hz
        eda = np.array([0.1] * 4, dtype=np.float32)
        ibi = np.array([800.0] * 4, dtype=np.float32)
        mapped = map_wesad_labels(labels, eda, ibi)
        assert np.all(mapped[:len(mapped)] == 0)  # calm

    def test_amusement_maps_to_mild(self):
        labels = np.array([3] * 700, dtype=np.int32)
        eda = np.array([0.1] * 4, dtype=np.float32)
        ibi = np.array([800.0] * 4, dtype=np.float32)
        mapped = map_wesad_labels(labels, eda, ibi)
        assert np.all(mapped[:len(mapped)] == 1)  # mild

    def test_undefined_maps_to_minus_one(self):
        labels = np.array([0] * 700, dtype=np.int32)
        eda = np.array([0.1] * 4, dtype=np.float32)
        ibi = np.array([800.0] * 4, dtype=np.float32)
        mapped = map_wesad_labels(labels, eda, ibi)
        assert np.all(mapped[:len(mapped)] == -1)

    def test_meditation_maps_to_minus_one(self):
        labels = np.array([4] * 700, dtype=np.int32)
        eda = np.array([0.1] * 4, dtype=np.float32)
        ibi = np.array([800.0] * 4, dtype=np.float32)
        mapped = map_wesad_labels(labels, eda, ibi)
        assert np.all(mapped[:len(mapped)] == -1)


class TestCreateWindows:
    def test_output_shape(self):
        features = np.random.randn(200, 5).astype(np.float32)
        labels = np.zeros(200, dtype=np.int32)
        X, y = create_windows(features, labels, window_size=30, step=15)
        assert X.ndim == 3
        assert X.shape[1] == 30
        assert X.shape[2] == 5
        assert X.shape[0] == y.shape[0]

    def test_windows_with_undefined_labels_are_skipped(self):
        features = np.random.randn(100, 5).astype(np.float32)
        labels = np.zeros(100, dtype=np.int32)
        labels[5:10] = -1  # mark some undefined
        X_clean, y_clean = create_windows(features, labels, window_size=30, step=15)
        X_all, y_all = create_windows(
            features, np.zeros(100, dtype=np.int32), window_size=30, step=15
        )
        assert len(X_clean) < len(X_all)


class TestNormalizeFeatures:
    def test_output_shape_preserved(self):
        X = np.random.randn(50, 30, 5).astype(np.float32)
        X_norm, means, stds = normalize_features(X)
        assert X_norm.shape == X.shape

    def test_returns_means_and_stds(self):
        X = np.random.randn(50, 30, 5).astype(np.float32)
        _, means, stds = normalize_features(X)
        assert means.shape == (5,)
        assert stds.shape == (5,)

    def test_apply_existing_params(self):
        X_train = np.random.randn(50, 30, 5).astype(np.float32) * 5 + 3
        _, means, stds = normalize_features(X_train)
        X_test = np.random.randn(10, 30, 5).astype(np.float32) * 5 + 3
        X_norm, _, _ = normalize_features(X_test, means=means, stds=stds)
        assert X_norm.shape == X_test.shape
