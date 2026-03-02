"""
Reproduction of ML results from:
"Integrated computational and machine learning study of elastic,
thermophysical, and ultrasonic properties of LiPb alloy"
by Anurag Singh et al., Computational Condensed Matter 45 (2025) e01162

Goal: Predict thermal conductivity (κ) of LiPb using Ridge, Random Forest,
SVR, and XGBoost with Leave-One-Temperature-Out Cross-Validation (LOTO-CV).
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("XGBoost not installed. Install with: pip install xgboost")

# =============================================================================
# DATA EXTRACTION FROM TABLES 1, 2, 3
# =============================================================================

temperatures = [100, 200, 300, 400, 500]  # Kelvin
directions = ['<100>', '<110>', '<111>']

# --- Table 1: SOECs and TOECs (GPa) - temperature dependent only ---
table1 = {
    'C11':  [55.98, 54.90, 53.81, 52.73, 51.64],
    'C12':  [4.53,  4.40,  4.28,  4.15,  4.02],
    'C44':  [4.53,  4.40,  4.28,  4.15,  4.03],
    'C111': [-86.74, -84.90, -83.05, -81.20, -79.35],
    'C112': [-29.55, -29.28, -28.96, -28.64, -28.33],
    'C123': [-26.60, -26.36, -26.12, -25.88, -25.64],
    'C144': [-26.46, -26.22, -25.98, -25.74, -25.50],
    'C166': [-29.52, -29.20, -28.89, -28.57, -28.25],
    'C456': [-26.54, -26.30, -26.06, -25.82, -25.58],
}

# --- Table 2: Velocities, thermal conductivity, relaxation times, coupling constants ---
# VL, VS1, VS2 in 10^3 m/s
# κ in 10^2 Wm^-1K^-1 (multiply by 100 for Wm^-1K^-1)
# τth in 10^-11 s
# DL, DS1, DS2 are acoustic coupling constants

table2 = {
    'VL': {
        '<100>': [2.68, 2.66, 2.63, 2.60, 2.58],
        '<110>': [2.12, 2.09, 2.07, 2.05, 2.02],
        '<111>': [1.89, 1.87, 1.85, 1.82, 1.57],
    },
    'VS1': {
        '<100>': [0.76, 0.75, 0.74, 0.73, 0.72],
        '<110>': [0.76, 0.75, 0.74, 0.73, 0.72],
        '<111>': [1.55, 1.53, 1.52, 1.50, 1.48],
    },
    'VS2': {
        '<100>': [0.76, 0.75, 0.74, 0.73, 0.72],
        '<110>': [1.82, 1.80, 1.78, 1.77, 1.75],
        '<111>': [1.55, 1.53, 1.52, 1.50, 1.48],
    },
    'kappa_raw': {  # in 10^2 Wm^-1K^-1, target variable
        '<100>': [0.21, 0.10, 0.06, 0.04, 0.03],
        '<110>': [1.33, 0.62, 0.38, 0.26, 0.19],
        '<111>': [2.49, 1.16, 0.72, 0.50, 0.37],
    },
    'DL': {
        '<100>': [10.37, 10.75, 11.16, 11.61, 12.09],
        '<110>': [2.98,  3.08,  3.19,  3.31,  3.45],
        '<111>': [2.92,  3.04,  3.17,  3.31,  3.46],
    },
    'DS1': {
        '<100>': [3.37, 3.52, 3.68, 3.86, 4.06],
        '<110>': [1.87, 1.95, 2.04, 2.14, 2.25],
        '<111>': [15.04, 15.38, 15.75, 16.15, 16.58],
    },
    'DS2': {
        '<100>': [3.36,  3.52,  3.68,  3.86,  4.06],
        '<110>': [28.31, 28.91, 29.56, 30.26, 31.01],
        '<111>': [15.04, 15.38, 15.75, 16.15, 16.58],
    },
}

# --- Table 3: Attenuation (all in 10^-15 Nps^2 m^-1) ---
table3 = {
    'alpha_th': {
        '<100>': [0.007, 0.007, 0.008, 0.008, 0.009],
        '<110>': [0.0006, 0.003, 0.0008, 0.0001, 0.0006],
        '<111>': [0.007, 0.003, 0.001, 0.0001, 0.0006],
    },
    'alpha_L': {
        '<100>': [5.50,  6.54,  7.01,  7.30,  7.55],
        '<110>': [12.92, 15.84, 17.22, 18.11, 18.86],
        '<111>': [13.09, 16.51, 18.29, 19.50, 20.56],
    },
    'alpha_S1': {
        '<100>': [38.75, 47.02, 51.51, 54.91, 58.18],
        '<110>': [86.25, 108.04, 119.87, 128.61, 136.43],
        '<111>': [61.11, 75.44,  81.70,  85.04,  87.43],
    },
    'alpha_S2': {
        '<100>': [38.75, 47.02,  51.51,  54.91,  58.18],
        '<110>': [96.62, 116.68, 124.66, 128.64, 131.07],
        '<111>': [61.11, 75.44,  81.70,  85.04,  87.43],
    },
    'alpha_total': {
        '<100>': [83.02,  100.59, 110.05, 117.13, 123.91],
        '<110>': [195.80, 240.56, 261.75, 275.36, 286.36],
        '<111>': [135.32, 167.40, 181.69, 189.58, 195.42],
    },
}


# =============================================================================
# COMPUTE τth FROM FORMULA: τth = 3κ / (Cv * VD^2)
# =============================================================================
# We compute Debye velocity VD for each (temp, direction) pair,
# then derive τth consistently using the paper's formula (Eq. 7).
# First, solve for Cv using <100> direction data where we have known τth.

def compute_VD_100(VL, VS1):
    """Debye velocity for <100> and <111> directions (Eq. 5)"""
    return (1.0/3.0 * (1.0/VL**3 + 2.0/VS1**3))**(-1.0/3.0)

def compute_VD_110(VL, VS1, VS2):
    """Debye velocity for <110> direction (Eq. 6)"""
    return (1.0/3.0 * (1.0/VL**3 + 1.0/VS1**3 + 1.0/VS2**3))**(-1.0/3.0)

# Known τth for <100> direction (from Table 2, in 10^-11 s)
tau_th_100_known = [9.54, 4.41, 2.76, 1.96, 1.48]

# κ for <100> in Wm^-1K^-1
kappa_100 = [x * 100 for x in table2['kappa_raw']['<100>']]  # [21, 10, 6, 4, 3]

# Compute VD for <100> at each temperature (in 10^3 m/s)
VD_100_list = []
for i in range(5):
    VL = table2['VL']['<100>'][i]
    VS1 = table2['VS1']['<100>'][i]
    VD = compute_VD_100(VL, VS1)
    VD_100_list.append(VD)

# Solve for Cv at each temperature: Cv = 3κ / (τth * VD^2)
# Units: κ in W/(m·K), τth in 10^-11 s = τth * 1e-11 s, VD in 10^3 m/s = VD * 1e3 m/s
Cv_list = []
for i in range(5):
    kappa = kappa_100[i]  # W/(m·K)
    tau = tau_th_100_known[i] * 1e-11  # seconds
    VD = VD_100_list[i] * 1e3  # m/s
    Cv = 3.0 * kappa / (tau * VD**2)
    Cv_list.append(Cv)

print("Derived Cv values at each temperature (J/(m^3·K)):")
for i, T in enumerate(temperatures):
    print(f"  T={T}K: Cv = {Cv_list[i]:.4e}")

# Now compute τth for ALL (temperature, direction) pairs
tau_th_computed = {'<100>': [], '<110>': [], '<111>': []}

for i in range(5):
    # <100>
    VD = VD_100_list[i] * 1e3
    kappa = table2['kappa_raw']['<100>'][i] * 100
    tau = 3.0 * kappa / (Cv_list[i] * VD**2)
    tau_th_computed['<100>'].append(tau / 1e-11)  # convert back to 10^-11 s units

    # <110>
    VL = table2['VL']['<110>'][i] * 1e3
    VS1_val = table2['VS1']['<110>'][i] * 1e3
    VS2_val = table2['VS2']['<110>'][i] * 1e3
    VD_110 = compute_VD_110(VL/1e3, VS1_val/1e3, VS2_val/1e3) * 1e3
    kappa = table2['kappa_raw']['<110>'][i] * 100
    tau = 3.0 * kappa / (Cv_list[i] * VD_110**2)
    tau_th_computed['<110>'].append(tau / 1e-11)

    # <111>
    VL = table2['VL']['<111>'][i] * 1e3
    VS1_val = table2['VS1']['<111>'][i] * 1e3
    VD_111 = compute_VD_100(VL/1e3, VS1_val/1e3) * 1e3
    kappa = table2['kappa_raw']['<111>'][i] * 100
    tau = 3.0 * kappa / (Cv_list[i] * VD_111**2)
    tau_th_computed['<111>'].append(tau / 1e-11)

print("\nComputed τth values (10^-11 s):")
for d in directions:
    print(f"  {d}: {[f'{x:.2f}' for x in tau_th_computed[d]]}")


# =============================================================================
# BUILD THE DATASET (15 samples: 5 temperatures × 3 directions)
# =============================================================================

rows = []
for j, d in enumerate(directions):
    for i, T in enumerate(temperatures):
        row = {'T': T, 'direction': d}

        # Table 1 features (temperature-dependent only)
        for key, values in table1.items():
            row[key] = values[i]

        # Table 2 features (direction + temperature dependent)
        for key in ['VL', 'VS1', 'VS2', 'DL', 'DS1', 'DS2']:
            row[key] = table2[key][d][i]

        # Computed τth
        row['tau_th'] = tau_th_computed[d][i]

        # Table 3 features
        for key in ['alpha_th', 'alpha_L', 'alpha_S1', 'alpha_S2', 'alpha_total']:
            row[key] = table3[key][d][i]

        # Target: κ in Wm^-1K^-1
        row['kappa'] = table2['kappa_raw'][d][i] * 100  # Convert from 10^2 units

        rows.append(row)

df = pd.DataFrame(rows)

print("\n" + "="*70)
print("DATASET OVERVIEW")
print("="*70)
print(f"Shape: {df.shape}")
print(f"\nSamples per direction:")
print(df['direction'].value_counts().to_string())
print(f"\nTarget (κ) statistics:")
print(df['kappa'].describe().to_string())
print(f"\nFull dataset:")
print(df[['T', 'direction', 'kappa']].to_string())

# =============================================================================
# FEATURE SELECTION
# =============================================================================
# The paper uses features from Tables 1-3 plus temperature.
# Based on feature importance plots (Fig. 8), the key features are:
# DL, VS1, VL, VS2, DS2, tau_th, T, DS1, alpha_over_v2_total

# We use all numeric features except direction (categorical) and target
feature_cols = [c for c in df.columns if c not in ['direction', 'kappa']]
X = df[feature_cols].values
y = df['kappa'].values

print(f"\nFeatures ({len(feature_cols)}):")
print(feature_cols)


# =============================================================================
# LEAVE-ONE-TEMPERATURE-OUT CROSS-VALIDATION (LOTO-CV)
# =============================================================================

def loto_cv(model_class, model_params, X, y, df, feature_cols):
    """
    Leave-One-Temperature-Out CV: for each temperature, train on remaining
    4 temperatures (12 samples) and predict the held-out temperature (3 samples).
    """
    all_preds = np.zeros(len(y))
    all_true = np.zeros(len(y))

    for T_out in temperatures:
        train_mask = df['T'] != T_out
        test_mask = df['T'] == T_out

        X_train = X[train_mask]
        y_train = y[train_mask]
        X_test = X[test_mask]
        y_test = y[test_mask]

        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model = model_class(**model_params)
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)

        all_preds[test_mask] = preds
        all_true[test_mask] = y_test

    mae = mean_absolute_error(all_true, all_preds)
    rmse = np.sqrt(mean_squared_error(all_true, all_preds))
    r2 = r2_score(all_true, all_preds)

    return mae, rmse, r2, all_preds, all_true


# =============================================================================
# TRAIN AND EVALUATE ALL MODELS
# =============================================================================

models = {
    'Ridge': (Ridge, {'alpha': 1.0}),
    'RandomForest': (RandomForestRegressor, {
        'n_estimators': 100, 'random_state': 42, 'max_depth': None
    }),
    'SVR': (SVR, {'kernel': 'rbf', 'C': 1.0, 'epsilon': 0.1}),
}

if HAS_XGBOOST:
    models['XGBoost'] = (XGBRegressor, {
        'n_estimators': 100, 'random_state': 42, 'max_depth': 3,
        'learning_rate': 0.1, 'verbosity': 0
    })

print("\n" + "="*70)
print("MODEL PERFORMANCE COMPARISON (LOTO-CV)")
print("="*70)

results = {}
predictions = {}

for name, (cls, params) in models.items():
    mae, rmse, r2, preds, true = loto_cv(cls, params, X, y, df, feature_cols)
    results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
    predictions[name] = (true, preds)
    print(f"\n{name}:")
    print(f"  MAE  = {mae:.2f} Wm⁻¹K⁻¹")
    print(f"  RMSE = {rmse:.2f} Wm⁻¹K⁻¹")
    print(f"  R²   = {r2:.4f}")

# =============================================================================
# PAPER'S REPORTED RESULTS (from text and Fig. 6)
# =============================================================================

print("\n" + "="*70)
print("PAPER'S REPORTED RESULTS (approximate, from text/figures)")
print("="*70)
print("Ridge:        MAE ≈ 21, R² ≈ 0.76")
print("RandomForest: R² ≈ 0.35-0.55")
print("SVR:          R² ≈ 0 (underfitting)")
print("XGBoost:      R² ≈ 0.35-0.55")

# =============================================================================
# COMPARISON TABLE
# =============================================================================

print("\n" + "="*70)
print("SIDE-BY-SIDE COMPARISON")
print("="*70)
print(f"{'Model':<15} {'Our MAE':>10} {'Our RMSE':>10} {'Our R²':>10}")
print("-" * 50)
for name in results:
    r = results[name]
    print(f"{name:<15} {r['MAE']:>10.2f} {r['RMSE']:>10.2f} {r['R2']:>10.4f}")


# =============================================================================
# RESIDUAL TABLE (like Table 4 in paper)
# =============================================================================

print("\n" + "="*70)
print("RESIDUAL TABLE (Ridge model, compare with Table 4)")
print("="*70)
true_vals, ridge_preds = predictions['Ridge']
print(f"{'T (K)':<8} {'Direction':<10} {'κ_ref':>12} {'κ_pred':>12} {'Δκ':>12}")
print("-" * 56)
for idx, row in df.iterrows():
    T = row['T']
    d = row['direction']
    k_ref = row['kappa']
    k_pred = ridge_preds[idx]
    delta = k_pred - k_ref
    print(f"{T:<8} {d:<10} {k_ref:>12.2f} {k_pred:>12.2f} {delta:>+12.2f}")


# =============================================================================
# FEATURE IMPORTANCE (Random Forest)
# =============================================================================

# Train RF on full dataset for feature importance
scaler_full = StandardScaler()
X_scaled = scaler_full.fit_transform(X)
rf_full = RandomForestRegressor(n_estimators=100, random_state=42)
rf_full.fit(X_scaled, y)

importances = rf_full.feature_importances_
sorted_idx = np.argsort(importances)[::-1]

print("\n" + "="*70)
print("RANDOM FOREST FEATURE IMPORTANCES (Top 10)")
print("="*70)
for rank, idx in enumerate(sorted_idx[:10]):
    print(f"  {rank+1}. {feature_cols[idx]:<20} {importances[idx]:.4f}")


# =============================================================================
# PLOTS
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Model Performance Comparison (LOTO-CV)\nReproduction of Singh et al. (2025)', fontsize=14)

for ax, (name, (true_vals, pred_vals)) in zip(axes.flat, predictions.items()):
    ax.scatter(true_vals, pred_vals, c='blue', alpha=0.7, edgecolors='black', s=60)
    lims = [0, max(max(true_vals), max(pred_vals)) * 1.1]
    ax.plot(lims, lims, 'r--', label='Ideal')
    ax.set_xlabel('True κ (W/mK)')
    ax.set_ylabel('Predicted κ (W/mK)')
    r2 = results[name]['R2']
    mae = results[name]['MAE']
    ax.set_title(f'{name} Parity Plot\nMAE={mae:.1f}, R²={r2:.3f}')
    ax.legend()
    ax.set_xlim(lims)
    ax.set_ylim(lims)

plt.tight_layout()
plt.savefig('/Users/tisenres/PycharmProjects/AlcoWatch/paper_reproduction/parity_plots.png', dpi=150)
print("\nParity plots saved to paper_reproduction/parity_plots.png")

# Bar chart comparison (like Fig. 6)
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
model_names = list(results.keys())
maes = [results[m]['MAE'] for m in model_names]
rmses = [results[m]['RMSE'] for m in model_names]
r2s = [results[m]['R2'] for m in model_names]

axes2[0].bar(model_names, maes, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'][:len(model_names)])
axes2[0].set_ylabel('MAE (W/mK)')
axes2[0].set_title('MAE (W/mK)')

axes2[1].bar(model_names, rmses, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'][:len(model_names)])
axes2[1].set_ylabel('RMSE (W/mK)')
axes2[1].set_title('RMSE (W/mK)')

axes2[2].bar(model_names, r2s, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'][:len(model_names)])
axes2[2].set_ylabel('R²')
axes2[2].set_title('R²')

fig2.suptitle('Model Performance Comparison (LOTO-CV)', fontsize=14)
plt.tight_layout()
plt.savefig('/Users/tisenres/PycharmProjects/AlcoWatch/paper_reproduction/performance_comparison.png', dpi=150)
print("Performance comparison saved to paper_reproduction/performance_comparison.png")

# Feature importance plot
fig3, ax3 = plt.subplots(figsize=(10, 6))
top_n = min(10, len(feature_cols))
top_idx = sorted_idx[:top_n]
ax3.barh(range(top_n), importances[top_idx][::-1])
ax3.set_yticks(range(top_n))
ax3.set_yticklabels([feature_cols[i] for i in top_idx][::-1])
ax3.set_xlabel('Feature Importance')
ax3.set_title('Random Forest Feature Importances')
plt.tight_layout()
plt.savefig('/Users/tisenres/PycharmProjects/AlcoWatch/paper_reproduction/feature_importances.png', dpi=150)
print("Feature importances saved to paper_reproduction/feature_importances.png")

plt.show()
print("\nDone!")
