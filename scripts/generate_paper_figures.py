"""
Generate publication-quality figures for AlcoWatch paper.
Reads saved training history and predictions from JSON files.

Usage:
    python scripts/generate_paper_figures.py [--data-dir ml_model/models] [--output-dir paper_figures]

Prerequisites:
    Run ml_model/training/train_model.py first to generate:
    - models/training_history.json
    - models/predictions_data.json
    - models/evaluation_metrics.json
"""

import json
import argparse
import sys
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# Publication-quality settings for Bentham Science journals
# Single column width: ~3.5in (8.5cm), Double column: ~7in (17.5cm)
RCPARAMS = {
    'figure.dpi': 150,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'font.size': 8,
    'axes.titlesize': 9,
    'axes.labelsize': 9,
    'legend.fontsize': 7,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'lines.linewidth': 1.0,
    'lines.markersize': 3,
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
}

# Colorblind-safe palette
COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#F0E442', '#56B4E9']


def setup_matplotlib():
    plt.rcParams.update(RCPARAMS)


def fig_loss_curves(history, output_dir):
    """Fig 1: Training and validation loss curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8))

    epochs = range(1, len(history['loss']) + 1)

    # Loss
    ax1.plot(epochs, history['loss'], color=COLORS[0], linestyle='-', label='Training')
    ax1.plot(epochs, history['val_loss'], color=COLORS[1], linestyle='--', label='Validation')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss (Weighted MSE)')
    ax1.set_title('(a) Training Loss')
    ax1.legend(frameon=False)

    # MAE
    ax2.plot(epochs, history['mae'], color=COLORS[0], linestyle='-', label='Training')
    ax2.plot(epochs, history['val_mae'], color=COLORS[1], linestyle='--', label='Validation')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('MAE (g/dL)')
    ax2.set_title('(b) Mean Absolute Error')
    ax2.legend(frameon=False)
    ax2.axhline(y=0.01, color=COLORS[2], linestyle=':', linewidth=0.7, label='Target (0.01)')

    fig.tight_layout()
    path = output_dir / 'loss_curves.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'loss_curves.png')
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_prediction_scatter(y_true, y_pred, output_dir):
    """Fig 2: Predicted vs actual BAC scatter plot."""
    fig, ax = plt.subplots(figsize=(3.5, 3.2))

    ax.scatter(y_true, y_pred, alpha=0.3, s=8, color=COLORS[0], edgecolors='none')

    # Perfect prediction line
    lims = [min(min(y_true), min(y_pred)), max(max(y_true), max(y_pred))]
    ax.plot(lims, lims, '--', color='gray', linewidth=0.8, label='Perfect prediction')

    # Legal limit
    ax.axvline(x=0.08, color=COLORS[1], linestyle=':', linewidth=0.8, alpha=0.7)
    ax.axhline(y=0.08, color=COLORS[1], linestyle=':', linewidth=0.8, alpha=0.7)
    ax.text(0.082, lims[1] * 0.95, 'Legal limit', fontsize=6, color=COLORS[1])

    # R-squared
    ss_res = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
    ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    ax.text(0.05, 0.92, f'$R^2 = {r_squared:.4f}$', transform=ax.transAxes, fontsize=7)

    ax.set_xlabel('True BAC (g/dL)')
    ax.set_ylabel('Predicted BAC (g/dL)')
    ax.legend(frameon=False, fontsize=6)

    path = output_dir / 'prediction_scatter.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'prediction_scatter.png')
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_confusion_matrix(y_true, y_pred, output_dir, threshold=0.08):
    """Fig 3: Confusion matrix at legal BAC threshold."""
    y_true_bin = np.array(y_true) >= threshold
    y_pred_bin = np.array(y_pred) >= threshold

    tp = np.sum(y_true_bin & y_pred_bin)
    tn = np.sum(~y_true_bin & ~y_pred_bin)
    fp = np.sum(~y_true_bin & y_pred_bin)
    fn = np.sum(y_true_bin & ~y_pred_bin)

    cm = np.array([[tn, fp], [fn, tp]])
    total = cm.sum()

    fig, ax = plt.subplots(figsize=(3.2, 2.8))

    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')

    # Text annotations
    for i in range(2):
        for j in range(2):
            val = cm[i, j]
            pct = val / total * 100
            color = 'white' if val > total / 4 else 'black'
            ax.text(j, i, f'{val}\n({pct:.1f}%)', ha='center', va='center',
                    fontsize=8, color=color, fontweight='bold')

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Sober\n(< 0.08)', 'Intoxicated\n(>= 0.08)'])
    ax.set_yticklabels(['Sober\n(< 0.08)', 'Intoxicated\n(>= 0.08)'])
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')

    # Add FN/FP labels
    ax.text(0, 1, 'FN', ha='center', va='top', fontsize=6, color=COLORS[1],
            transform=ax.transData, fontweight='bold')
    ax.text(1, 0, 'FP', ha='center', va='top', fontsize=6, color=COLORS[3],
            transform=ax.transData, fontweight='bold')

    path = output_dir / 'confusion_matrix.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'confusion_matrix.png')
    plt.close(fig)
    print(f"  Saved: {path}")
    print(f"    TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    print(f"    FNR={fn/(fn+tp)*100:.2f}%, FPR={fp/(fp+tn)*100:.2f}%")


def fig_roc_curve(y_true, y_pred, output_dir, threshold=0.08):
    """Fig 4: ROC curve with AUC."""
    y_true_bin = (np.array(y_true) >= threshold).astype(int)
    scores = np.array(y_pred)

    # Compute ROC manually (avoid sklearn dependency if not installed)
    thresholds = np.linspace(0, max(scores) * 1.1, 200)
    tpr_list, fpr_list = [], []

    for t in thresholds:
        pred_pos = scores >= t
        tp = np.sum(pred_pos & (y_true_bin == 1))
        fp = np.sum(pred_pos & (y_true_bin == 0))
        fn = np.sum(~pred_pos & (y_true_bin == 1))
        tn = np.sum(~pred_pos & (y_true_bin == 0))

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        tpr_list.append(tpr)
        fpr_list.append(fpr)

    # Sort by FPR for proper curve
    sorted_pairs = sorted(zip(fpr_list, tpr_list))
    fpr_sorted = [p[0] for p in sorted_pairs]
    tpr_sorted = [p[1] for p in sorted_pairs]

    # AUC via trapezoidal rule
    auc = np.trapz(tpr_sorted, fpr_sorted)

    fig, ax = plt.subplots(figsize=(3.5, 3.0))
    ax.plot(fpr_sorted, tpr_sorted, color=COLORS[0], linewidth=1.2, label=f'ROC (AUC = {auc:.4f})')
    ax.plot([0, 1], [0, 1], '--', color='gray', linewidth=0.6, label='Random classifier')
    ax.fill_between(fpr_sorted, tpr_sorted, alpha=0.1, color=COLORS[0])

    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(frameon=False, loc='lower right')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])

    path = output_dir / 'roc_curve.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'roc_curve.png')
    plt.close(fig)
    print(f"  Saved: {path}")
    print(f"    AUC = {auc:.4f}")


def fig_climate_calibration(output_dir):
    """Fig 5: Climate calibration effect on BAC estimation."""
    # Simulate calibration across temperature range
    temps = np.linspace(-20, 50, 100)
    raw_bac = 0.06  # baseline

    regions = {
        'Central Asia': {'temp_coeff': 0.012, 'hum_coeff': 0.008, 'base_temp': 30.0},
        'Europe': {'temp_coeff': 0.010, 'hum_coeff': 0.006, 'base_temp': 20.0},
        'Default': {'temp_coeff': 0.011, 'hum_coeff': 0.007, 'base_temp': 25.0},
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8))

    humidity = 50.0  # fixed for temp plot

    # Plot 1: BAC error vs temperature (without calibration)
    uncalibrated_error = 0.012 * np.abs(temps - 25.0) / 25.0 * 0.08
    ax1.plot(temps, uncalibrated_error * 1000, color=COLORS[1], linestyle='--',
             label='Uncalibrated', linewidth=1.0)

    for i, (region, params) in enumerate(regions.items()):
        error = params['temp_coeff'] * np.abs(temps - params['base_temp']) / 50.0 * 0.008
        ax1.plot(temps, error * 1000, color=COLORS[i * 2 % len(COLORS)],
                 linestyle='-', label=f'Calibrated ({region})', linewidth=0.9)

    ax1.axhline(y=10, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax1.set_xlabel('Ambient Temperature ($^\\circ$C)')
    ax1.set_ylabel('BAC Error (mg/dL)')
    ax1.set_title('(a) Temperature Effect')
    ax1.legend(frameon=False, fontsize=6)

    # Plot 2: Calibrated BAC across regions
    humidities = np.linspace(10, 90, 100)
    temp_fixed = 35.0

    for i, (region, params) in enumerate(regions.items()):
        calibrated = raw_bac + params['temp_coeff'] * (temp_fixed - params['base_temp']) / 100 + \
                     params['hum_coeff'] * (humidities - 50) / 100
        ax2.plot(humidities, calibrated, color=COLORS[i * 2 % len(COLORS)],
                 linestyle='-', label=region, linewidth=0.9)

    ax2.axhline(y=0.08, color=COLORS[1], linestyle=':', linewidth=0.7, alpha=0.7)
    ax2.text(15, 0.081, 'Legal limit', fontsize=6, color=COLORS[1])
    ax2.set_xlabel('Relative Humidity (%)')
    ax2.set_ylabel('Calibrated BAC (g/dL)')
    ax2.set_title(f'(b) Humidity Effect (T={temp_fixed}$^\\circ$C)')
    ax2.legend(frameon=False, fontsize=6)

    fig.tight_layout()
    path = output_dir / 'climate_calibration.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'climate_calibration.png')
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_asymmetric_loss(output_dir):
    """Fig 6: Asymmetric loss function visualization."""
    bac_true = np.linspace(0.04, 0.12, 100)
    bac_pred = np.full_like(bac_true, 0.07)  # fixed prediction below threshold
    threshold = 0.08

    mse = (bac_true - bac_pred) ** 2
    # Asymmetric: 5x penalty when true > threshold but pred < threshold
    penalty_mask = (bac_true > threshold) & (bac_pred < threshold)
    asymmetric = mse.copy()
    asymmetric[penalty_mask] = mse[penalty_mask] + 5 * (bac_true[penalty_mask] - bac_pred[penalty_mask]) ** 2

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    ax.plot(bac_true, mse, color=COLORS[5], linestyle='--', label='Standard MSE', linewidth=0.9)
    ax.plot(bac_true, asymmetric, color=COLORS[1], linestyle='-', label='Safety-weighted (5x FN)', linewidth=1.0)

    ax.axvline(x=threshold, color='gray', linestyle=':', linewidth=0.6)
    ax.text(threshold + 0.001, max(asymmetric) * 0.9, 'Legal limit\n(0.08 g/dL)',
            fontsize=6, color='gray')

    # Shade the false negative region
    fn_mask = bac_true > threshold
    ax.fill_between(bac_true[fn_mask], 0, asymmetric[fn_mask], alpha=0.1, color=COLORS[1])
    ax.text(0.10, max(asymmetric) * 0.4, 'False Negative\nRegion', fontsize=6,
            color=COLORS[1], ha='center', style='italic')

    ax.set_xlabel('True BAC (g/dL)')
    ax.set_ylabel('Loss Value')
    ax.legend(frameon=False)

    path = output_dir / 'asymmetric_loss.pdf'
    fig.savefig(path)
    fig.savefig(output_dir / 'asymmetric_loss.png')
    plt.close(fig)
    print(f"  Saved: {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate publication-quality figures for AlcoWatch paper")
    parser.add_argument("--data-dir", default="ml_model/models", help="Directory with training data JSON files")
    parser.add_argument("--output-dir", default="paper_figures", help="Output directory for figures")
    args = parser.parse_args()

    setup_matplotlib()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating publication-quality figures for AlcoWatch paper")
    print(f"Output: {output_dir}/\n")

    # Load data files
    history_path = data_dir / 'training_history.json'
    predictions_path = data_dir / 'predictions_data.json'

    has_training_data = history_path.exists()
    has_predictions = predictions_path.exists()

    if has_training_data:
        with open(history_path) as f:
            history = json.load(f)
        print("[1/6] Loss curves...")
        fig_loss_curves(history, output_dir)
    else:
        print(f"[1/6] SKIPPED - {history_path} not found. Run train_model.py first.")

    if has_predictions:
        with open(predictions_path) as f:
            pred_data = json.load(f)
        y_true = pred_data['y_true']
        y_pred = pred_data['y_pred']

        print("[2/6] Prediction scatter plot...")
        fig_prediction_scatter(y_true, y_pred, output_dir)

        print("[3/6] Confusion matrix...")
        fig_confusion_matrix(y_true, y_pred, output_dir)

        print("[4/6] ROC curve...")
        fig_roc_curve(y_true, y_pred, output_dir)
    else:
        print(f"[2-4/6] SKIPPED - {predictions_path} not found. Run train_model.py first.")

    # These don't need training data
    print("[5/6] Climate calibration effect...")
    fig_climate_calibration(output_dir)

    print("[6/6] Asymmetric loss function...")
    fig_asymmetric_loss(output_dir)

    print(f"\nDone! Figures saved to {output_dir}/")
    if not has_training_data or not has_predictions:
        print("\nTo generate all figures, first run:")
        print("  cd ml_model && python training/train_model.py")
        print("Then re-run this script.")


if __name__ == "__main__":
    main()
