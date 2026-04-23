import numpy as np
from scipy import signal as scipy_signal
from typing import Tuple, Optional


def resample_to_4hz(arr: np.ndarray, source_hz: int) -> np.ndarray:
    """Resample 1-D signal from source_hz to 4 Hz."""
    if source_hz == 4:
        return arr
    n_out = int(len(arr) * 4 / source_hz)
    return scipy_signal.resample(arr, n_out).astype(np.float32)


def compute_ibi(bvp_4hz: np.ndarray) -> np.ndarray:
    """
    Estimate IBI (ms) from BVP at 4 Hz.
    Returns forward-filled IBI series of same length as input.
    """
    peaks, _ = scipy_signal.find_peaks(bvp_4hz, distance=2)  # min 0.5s gap
    ibi_series = np.full(len(bvp_4hz), 800.0, dtype=np.float32)  # default resting
    for i in range(1, len(peaks)):
        ibi_ms = (peaks[i] - peaks[i - 1]) / 4.0 * 1000.0
        ibi_series[peaks[i - 1]:peaks[i]] = ibi_ms
    if len(peaks) > 0:
        ibi_series[peaks[-1]:] = ibi_series[max(0, peaks[-1] - 1)]
    return ibi_series


def map_wesad_labels(
    labels_700hz: np.ndarray,
    eda_4hz: np.ndarray,
    ibi_4hz: np.ndarray,
) -> np.ndarray:
    """
    Map WESAD 700 Hz labels → 4-class driving stress at 4 Hz.

    WESAD: 0=undefined, 1=baseline, 2=stress, 3=amusement, 4=meditation
    Output: 0=calm, 1=mild, 2=moderate, 3=critical, -1=discard

    Stress split rule: samples where EDA > 75th pct AND IBI < 25th pct → critical (3),
    remaining stress samples → moderate (2).
    """
    factor = 700 // 4  # 175 samples per 4 Hz slot
    n_out = len(labels_700hz) // factor
    labels_4hz = np.array([
        np.bincount(np.clip(labels_700hz[i * factor:(i + 1) * factor], 0, 4)).argmax()
        for i in range(n_out)
    ], dtype=np.int32)

    length = min(len(labels_4hz), len(eda_4hz), len(ibi_4hz))
    labels_4hz = labels_4hz[:length]
    eda = eda_4hz[:length]
    ibi = ibi_4hz[:length]

    stress_mask = labels_4hz == 2
    if stress_mask.sum() > 0:
        eda_75 = np.percentile(eda[stress_mask], 75)
        ibi_25 = np.percentile(ibi[stress_mask], 25)
    else:
        eda_75, ibi_25 = np.inf, 0.0

    mapped = np.full(length, -1, dtype=np.int32)
    mapped[labels_4hz == 1] = 0  # baseline → calm
    mapped[labels_4hz == 3] = 1  # amusement → mild
    moderate = stress_mask & ~((eda > eda_75) & (ibi < ibi_25))
    critical = stress_mask & (eda > eda_75) & (ibi < ibi_25)
    mapped[moderate] = 2
    mapped[critical] = 3
    return mapped


def create_windows(
    features: np.ndarray,
    labels: np.ndarray,
    window_size: int = 30,
    step: int = 15,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sliding window segmentation.
    features: [N, n_features]   labels: [N]
    Returns (X, y): X shape [windows, window_size, n_features]
    Windows containing any label == -1 are discarded.
    """
    X, y = [], []
    for start in range(0, len(features) - window_size + 1, step):
        end = start + window_size
        window_labels = labels[start:end]
        if np.any(window_labels == -1):
            continue
        label = int(np.bincount(window_labels, minlength=4).argmax())
        X.append(features[start:end])
        y.append(label)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def normalize_features(
    X: np.ndarray,
    means: Optional[np.ndarray] = None,
    stds: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Z-score normalization per feature channel across [N, T, F] array.
    Returns (X_normalized, means, stds). Pass means/stds to apply train stats to test.
    """
    if means is None:
        means = X.mean(axis=(0, 1))
        stds = X.std(axis=(0, 1)) + 1e-8
    return ((X - means) / stds).astype(np.float32), means, stds
