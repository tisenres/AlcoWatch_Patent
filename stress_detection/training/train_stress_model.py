"""
Full WESAD training pipeline for driver stress detection.
Usage: python -m stress_detection.training.train_stress_model
Outputs: stress_detection/models/stress_model.tflite + stress_metrics.json
"""
import os
import sys
import json
import time
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from stress_detection.data.wesad_loader import WESADLoader
from stress_detection.data.feature_engineering import (
    resample_to_4hz, compute_ibi, map_wesad_labels,
    create_windows, normalize_features,
)
from stress_detection.training.stress_model import StressClassificationModel

DATA_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'WESAD')
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
WINDOW_SIZE = 30
STEP        = 15
EPOCHS      = 60
BATCH_SIZE  = 32
CLASS_NAMES = ['Calm', 'Mild', 'Moderate', 'Critical']


def build_dataset(loader: WESADLoader):
    X_all, y_all = [], []
    for subj in loader.available_subjects():
        print(f"  Loading {subj}...", end=' ')
        try:
            d = loader.load_subject(subj)
        except Exception as e:
            print(f"SKIP ({e})")
            continue

        bvp  = resample_to_4hz(d['BVP'], 64)
        eda  = d['EDA']
        temp = d['TEMP']
        acc  = resample_to_4hz(d['ACC'], 32)
        ibi  = compute_ibi(bvp)

        labels = map_wesad_labels(d['labels'], eda, ibi)

        n = min(len(bvp), len(eda), len(temp), len(acc), len(ibi), len(labels))
        features = np.stack([bvp[:n], eda[:n], temp[:n], acc[:n], ibi[:n]], axis=1)

        X, y = create_windows(features, labels[:n], WINDOW_SIZE, STEP)
        if len(X) == 0:
            print("no windows")
            continue
        X_all.append(X)
        y_all.append(y)
        print(f"{len(X)} windows  classes={np.bincount(y, minlength=4)}")

    return np.concatenate(X_all), np.concatenate(y_all)


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("=== Driver Stress Detection — Training ===\n")

    loader = WESADLoader(DATA_DIR)
    print("Building dataset...")
    X, y = build_dataset(loader)
    print(f"\nTotal: {len(X)} windows | class distribution: {np.bincount(y, minlength=4)}\n")

    X_norm, means, stds = normalize_features(X)
    np.save(os.path.join(MODELS_DIR, 'scaler_means.npy'), means)
    np.save(os.path.join(MODELS_DIR, 'scaler_stds.npy'), stds)

    X_train, X_test, y_train, y_test = train_test_split(
        X_norm, y, test_size=0.2, random_state=42, stratify=y
    )
    y_train_cat = tf.keras.utils.to_categorical(y_train, 4)
    y_test_cat  = tf.keras.utils.to_categorical(y_test,  4)

    sm = StressClassificationModel()
    sm.compile()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True,
                                         monitor='val_accuracy'),
        tf.keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5, verbose=1),
    ]
    history = sm.model.fit(
        X_train, y_train_cat,
        validation_split=0.15,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )

    y_pred = np.argmax(sm.model.predict(X_test, verbose=0), axis=1)
    report_dict = classification_report(
        y_test, y_pred, target_names=CLASS_NAMES, output_dict=True
    )
    print("\n" + classification_report(y_test, y_pred, target_names=CLASS_NAMES))
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Inference latency (100 samples average)
    sample = X_test[:1]
    t0 = time.perf_counter()
    for _ in range(100):
        sm.model.predict(sample, verbose=0)
    latency_ms = (time.perf_counter() - t0) / 100 * 1000

    metrics = {
        'accuracy':        report_dict['accuracy'],
        'f1_macro':        report_dict['macro avg']['f1-score'],
        'per_class':       {k: v for k, v in report_dict.items() if k in CLASS_NAMES},
        'confusion_matrix': cm,
        'latency_ms':      round(latency_ms, 2),
        'train_history':   {k: [float(v) for v in vs]
                            for k, vs in history.history.items()},
    }
    with open(os.path.join(MODELS_DIR, 'stress_metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

    saved_model_dir = os.path.join(MODELS_DIR, 'stress_model_saved')
    sm.model.export(saved_model_dir)

    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]
    tflite_bytes = converter.convert()
    tflite_path = os.path.join(MODELS_DIR, 'stress_model.tflite')
    with open(tflite_path, 'wb') as f:
        f.write(tflite_bytes)
    size_kb = len(tflite_bytes) / 1024
    print(f"\nTFLite saved: {tflite_path} ({size_kb:.1f} KB)")
    print(f"Inference latency (CPU): {latency_ms:.1f} ms")

    # Quality gates
    assert report_dict['accuracy'] > 0.90, \
        f"Accuracy {report_dict['accuracy']:.3f} < 0.90 — model needs tuning"
    assert report_dict['macro avg']['f1-score'] > 0.88, \
        f"F1 macro {report_dict['macro avg']['f1-score']:.3f} < 0.88"
    assert size_kb < 80, f"TFLite {size_kb:.1f} KB > 80 KB limit"
    print("\nAll quality gates PASSED.")


if __name__ == '__main__':
    main()
