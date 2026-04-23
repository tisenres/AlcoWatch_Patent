"""
Generate paper figures from trained stress model metrics.
Run after training: python scripts/generate_stress_figures.py
Output: paper_figures/stress/
"""
import os
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

REPO_ROOT    = Path(__file__).resolve().parent.parent
METRICS_FILE = REPO_ROOT / 'stress_detection' / 'models' / 'stress_metrics.json'
OUTPUT_DIR   = REPO_ROOT / 'paper_figures' / 'stress'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CLASS_NAMES = ['Calm', 'Mild', 'Moderate', 'Critical']


def save(name):
    for ext in ('pdf', 'png'):
        plt.savefig(OUTPUT_DIR / f'{name}.{ext}', bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Saved: {name}.pdf")


def plot_confusion_matrix(metrics):
    cm = np.array(metrics['confusion_matrix'])
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = np.divide(cm.astype(float), row_sums,
                        out=np.zeros_like(cm, dtype=float),
                        where=row_sums != 0)
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax,
                linewidths=0.5, linecolor='white')
    ax.set_xlabel('Predicted Label', fontsize=12)
    ax.set_ylabel('True Label', fontsize=12)
    ax.set_title(
        f'Stress Classification — Confusion Matrix\n'
        f'Accuracy: {metrics["accuracy"]*100:.1f}%  |  F1 macro: {metrics["f1_macro"]:.3f}',
        fontsize=12
    )
    plt.tight_layout()
    save('confusion_matrix')


def plot_training_history(metrics):
    h = metrics['train_history']
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(h['loss'],      label='Train',      color='#2196F3', lw=2)
    ax1.plot(h['val_loss'],  label='Validation', color='#FF5722', lw=2, linestyle='--')
    ax1.set_xlabel('Epoch'); ax1.set_ylabel('Loss')
    ax1.set_title('Categorical Cross-Entropy Loss'); ax1.legend()
    ax2.plot(h['accuracy'],     label='Train',      color='#2196F3', lw=2)
    ax2.plot(h['val_accuracy'], label='Validation', color='#FF5722', lw=2, linestyle='--')
    ax2.set_xlabel('Epoch'); ax2.set_ylabel('Accuracy')
    ax2.set_title('Classification Accuracy'); ax2.legend()
    plt.tight_layout()
    save('training_history')


def plot_model_architecture():
    fig, ax = plt.subplots(figsize=(13, 3))
    ax.axis('off')
    blocks = [
        ('Input\n[1, 30, 5]', '#E3F2FD', '#1565C0'),
        ('BiLSTM\n64 units\n→[30,128]', '#E8F5E9', '#2E7D32'),
        ('Dropout\n0.3', '#FFF8E1', '#F57F17'),
        ('Attention\n×128', '#F3E5F5', '#6A1B9A'),
        ('Dense\n64, ReLU', '#E3F2FD', '#1565C0'),
        ('Dense\n32, ReLU', '#E3F2FD', '#1565C0'),
        ('Softmax\n4 classes', '#FCE4EC', '#880E4F'),
    ]
    w, h = 0.12, 0.6
    for i, (label, fc, ec) in enumerate(blocks):
        x = 0.07 + i * 0.135
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - w/2, 0.2), w, h, boxstyle='round,pad=0.015', fc=fc, ec=ec, lw=1.8
        ))
        ax.text(x, 0.5, label, ha='center', va='center', fontsize=8.5, fontweight='bold')
        if i < len(blocks) - 1:
            ax.annotate('', xy=(x + w/2 + 0.01, 0.5), xytext=(x + w/2, 0.5),
                        arrowprops=dict(arrowstyle='->', color='#555', lw=1.8))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title('BiLSTM + Attention Stress Classifier Architecture', fontsize=12, pad=8)
    plt.tight_layout()
    save('model_architecture')


def plot_system_overview():
    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.axis('off')
    components = [
        ('Wear OS\nSensors\nPPG · EDA\nTemp · ACC', '#E8F5E9', '#2E7D32'),
        ('TFLite\nStress\nClassifier\n[30 × 5]', '#E3F2FD', '#1565C0'),
        ('BLE\nTransmit\n12-byte\npacket', '#FFF3E0', '#E65100'),
        ('Arduino\nCabin\nController\nFSM', '#FCE4EC', '#880E4F'),
        ('Adaptive\nEnvironment\nLight · Fan\nAudio', '#F3E5F5', '#4A148C'),
    ]
    w = 0.15
    for i, (label, fc, ec) in enumerate(components):
        x = 0.1 + i * 0.2
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - w/2, 0.1), w, 0.8, boxstyle='round,pad=0.02', fc=fc, ec=ec, lw=2
        ))
        ax.text(x, 0.5, label, ha='center', va='center', fontsize=9, fontweight='bold')
        if i < len(components) - 1:
            ax.annotate('', xy=(x + w/2 + 0.02, 0.5), xytext=(x + w/2, 0.5),
                        arrowprops=dict(arrowstyle='->', color='#444', lw=2.5))
    ax.set_xlim(0, 1.05); ax.set_ylim(0, 1)
    ax.set_title('End-to-End System: Sensor → Inference → BLE → Cabin Control', fontsize=11, pad=8)
    plt.tight_layout()
    save('system_overview')


if __name__ == '__main__':
    with open(METRICS_FILE) as f:
        metrics = json.load(f)
    plot_confusion_matrix(metrics)
    plot_training_history(metrics)
    plot_model_architecture()
    plot_system_overview()
    print(f"\nAll figures saved to {OUTPUT_DIR}/")
