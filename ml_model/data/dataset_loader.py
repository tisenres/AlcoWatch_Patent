"""
Dataset loader for alcohol sensor data
Generates physiologically realistic synthetic data using Widmark pharmacokinetic model
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path
from sklearn.model_selection import train_test_split


class AlcoholDatasetLoader:
    """
    Generates and preprocesses synthetic alcohol sensor datasets using
    Widmark pharmacokinetic BAC curves with per-subject physiological baselines.
    """

    def __init__(self, data_dir: str = "./data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scaler_params = None  # Will store mean/std after normalization

    def create_synthetic_dataset(
        self,
        n_subjects: int = 50,
        sessions_per_subject: int = 5,
        noise_level: float = 0.05
    ) -> pd.DataFrame:
        """
        Create synthetic alcohol sensor data using Widmark pharmacokinetic model.

        Each subject has consistent physiological baselines and multiple drinking
        sessions with diverse BAC profiles (light, moderate, heavy).

        Args:
            n_subjects: Number of simulated subjects
            sessions_per_subject: Average sessions per subject (varies +-2)
            noise_level: Sensor noise magnitude

        Returns:
            DataFrame with synthetic sensor data and BAC labels
        """
        np.random.seed(42)

        all_records = []
        session_counter = 0
        base_time = pd.Timestamp('2024-01-01')

        for subj_id in range(1, n_subjects + 1):
            # Per-subject physiological baselines
            is_male = np.random.random() < 0.5
            body_weight = np.random.uniform(60, 95) if is_male else np.random.uniform(50, 80)
            water_ratio = np.random.uniform(0.55, 0.68) if is_male else np.random.uniform(0.49, 0.58)
            elimination_rate = np.random.normal(0.015, 0.003)  # g/dL per hour
            elimination_rate = np.clip(elimination_rate, 0.010, 0.025)

            # Subject-specific baselines
            hr_baseline = np.random.uniform(62, 82)
            eda_baseline = np.random.uniform(2.0, 5.0)
            temp_baseline = np.random.uniform(32.5, 34.0)

            n_sessions = max(3, sessions_per_subject + np.random.randint(-2, 3))

            for sess_idx in range(n_sessions):
                session_counter += 1

                # Choose drinking profile
                profile = np.random.choice(
                    ['sober', 'light', 'moderate', 'heavy'],
                    p=[0.15, 0.25, 0.35, 0.25]
                )

                # Alcohol dose in grams based on profile
                if profile == 'sober':
                    alcohol_grams = 0.0
                elif profile == 'light':
                    alcohol_grams = np.random.uniform(10, 25)   # ~1-2 drinks
                elif profile == 'moderate':
                    alcohol_grams = np.random.uniform(30, 55)   # ~2-4 drinks
                else:  # heavy
                    alcohol_grams = np.random.uniform(60, 100)  # ~4-7 drinks

                # Session duration: 4-8 hours at 30-second intervals
                duration_hours = np.random.uniform(4, 8)
                n_points = int(duration_hours * 3600 / 30)  # 30-second intervals
                time_hours = np.linspace(0, duration_hours, n_points)
                timestamps = [base_time + pd.Timedelta(seconds=30 * i + session_counter * 50000)
                              for i in range(n_points)]

                # Widmark BAC curve
                if alcohol_grams == 0:
                    bac = np.zeros(n_points)
                else:
                    peak_bac = alcohol_grams / (water_ratio * body_weight * 10)
                    # Absorption phase (exponential rise, ~30-90 min to peak)
                    absorption_time = np.random.uniform(0.5, 1.5)  # hours to peak
                    absorption_rate = 1.0 / absorption_time

                    bac = np.zeros(n_points)
                    for i, t in enumerate(time_hours):
                        absorbed = peak_bac * (1 - np.exp(-absorption_rate * t))
                        eliminated = elimination_rate * t
                        bac[i] = max(0, absorbed - eliminated)

                # Add small per-sample physiological noise to BAC
                bac += np.random.normal(0, 0.002, n_points)
                bac = np.clip(bac, 0, 0.35)

                # Generate correlated physiological signals
                # PPG heart rate: baseline + alcohol effect + noise
                hr = hr_baseline + bac * 120 + np.random.normal(0, noise_level * 5, n_points)
                hr = np.clip(hr, 50, 160)

                # PPG quality: decreases with intoxication (motion artifacts)
                ppg_quality = 0.95 - bac * 2.5 + np.random.normal(0, noise_level * 0.3, n_points)
                ppg_quality = np.clip(ppg_quality, 0.5, 1.0)

                # EDA: increases with sympathetic activation from alcohol
                eda = eda_baseline + bac * 80 + np.random.normal(0, noise_level * 3, n_points)
                eda = np.clip(eda, 1.0, 20.0)

                # Skin temperature: increases with vasodilation
                skin_temp = temp_baseline + bac * 15 + np.random.normal(0, noise_level * 2, n_points)
                skin_temp = np.clip(skin_temp, 31.0, 38.0)

                # Environmental factors (stable within session, slight drift)
                ambient_temp = np.random.uniform(18, 32) + np.random.normal(0, 0.5, n_points).cumsum() * 0.01
                ambient_temp = np.clip(ambient_temp, 15, 40)
                humidity = np.random.uniform(25, 75) + np.random.normal(0, 0.3, n_points).cumsum() * 0.01
                humidity = np.clip(humidity, 15, 90)

                session_df = pd.DataFrame({
                    'timestamp': timestamps,
                    'ppg_heart_rate': hr,
                    'ppg_quality': ppg_quality,
                    'eda_value': eda,
                    'skin_temperature': skin_temp,
                    'ambient_temperature': ambient_temp,
                    'humidity': humidity,
                    'bac_true': bac,
                    'subject_id': subj_id,
                    'session_id': session_counter,
                    'profile': profile,
                })
                all_records.append(session_df)

        df = pd.concat(all_records, ignore_index=True)
        print(f"Generated {len(df)} samples across {session_counter} sessions, "
              f"{n_subjects} subjects")
        return df

    def preprocess_data(
        self,
        df: pd.DataFrame,
        normalize: bool = True,
        remove_outliers: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess sensor data for model training.

        Args:
            df: Raw sensor data
            normalize: Whether to z-score normalize the 6 model input features
            remove_outliers: Whether to remove statistical outliers

        Returns:
            Preprocessed DataFrame
        """
        df_clean = df.copy()

        # Remove outliers using IQR method
        if remove_outliers:
            for col in ['ppg_heart_rate', 'eda_value', 'skin_temperature']:
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_clean = df_clean[
                    (df_clean[col] >= lower_bound) &
                    (df_clean[col] <= upper_bound)
                ]

        # Z-score normalize only the 6 model input features
        if normalize:
            feature_cols = [
                'ppg_heart_rate', 'ppg_quality', 'eda_value',
                'skin_temperature', 'ambient_temperature', 'humidity',
            ]
            means = df_clean[feature_cols].mean()
            stds = df_clean[feature_cols].std()
            stds = stds.replace(0, 1)  # avoid division by zero

            self.scaler_params = {
                'mean': {col: float(means[col]) for col in feature_cols},
                'std': {col: float(stds[col]) for col in feature_cols},
            }

            df_clean[feature_cols] = (df_clean[feature_cols] - means) / stds

        return df_clean

    def create_sequences(
        self,
        df: pd.DataFrame,
        sequence_length: int = 10,
        target_col: str = 'bac_true'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time-series model training, grouped by session.

        Args:
            df: Preprocessed data
            sequence_length: Number of time steps in each sequence
            target_col: Target variable column name

        Returns:
            X (sequences), y (targets)
        """
        feature_cols = [
            'ppg_heart_rate', 'ppg_quality', 'eda_value',
            'skin_temperature', 'ambient_temperature', 'humidity'
        ]

        X_sequences = []
        y_targets = []

        for session_id in df['session_id'].unique():
            session_data = df[df['session_id'] == session_id].sort_values('timestamp')

            if len(session_data) < sequence_length + 1:
                continue

            for i in range(len(session_data) - sequence_length):
                X_seq = session_data.iloc[i:i+sequence_length][feature_cols].values
                y_target = session_data.iloc[i+sequence_length][target_col]

                X_sequences.append(X_seq)
                y_targets.append(y_target)

        return np.array(X_sequences), np.array(y_targets)

    def get_train_test_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.15,
        val_size: float = 0.15
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train, validation, and test sets."""
        # First split: train+val vs test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Second split: train vs val
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=42
        )

        return X_train, X_val, X_test, y_train, y_val, y_test


if __name__ == "__main__":
    loader = AlcoholDatasetLoader()

    print("Creating synthetic dataset with Widmark curves...")
    df = loader.create_synthetic_dataset(n_subjects=50, sessions_per_subject=5)

    print("\nPreprocessing data...")
    df_processed = loader.preprocess_data(df, normalize=True)

    print("Creating sequences...")
    X, y = loader.create_sequences(df_processed, sequence_length=10)

    print("Splitting data...")
    X_train, X_val, X_test, y_train, y_val, y_test = loader.get_train_test_split(X, y)

    print(f"\nDataset Statistics:")
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Input shape: {X_train.shape}")
    print(f"BAC range: {y_train.min():.4f} - {y_train.max():.4f}")
    print(f"BAC > 0.08 ratio: {(y_train > 0.08).mean():.2%}")
