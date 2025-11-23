"""
Dataset loader for alcohol sensor data
Integrates public datasets for BAC estimation model training
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path
import requests
from sklearn.model_selection import train_test_split


class AlcoholDatasetLoader:
    """
    Loads and preprocesses alcohol sensor datasets from public sources

    Key datasets:
    1. MMASH (Multilevel Monitoring of Activity and Sleep in Healthy people)
    2. WESAD (Wearable Stress and Affect Detection)
    3. AffectiveROAD (PPG and alcohol consumption data)
    4. Synthetic transdermal alcohol data
    """

    def __init__(self, data_dir: str = "./data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_datasets(self):
        """Download public datasets if not already present"""
        print("Downloading public alcohol and physiological datasets...")

        # Note: In practice, these would be real dataset URLs
        # For now, we'll create synthetic data structure
        datasets = {
            'transdermal_alcohol': 'https://example.com/tac_data.csv',
            'ppg_eda_combined': 'https://example.com/ppg_eda.csv',
            'wesad_subset': 'https://example.com/wesad.csv'
        }

        print("Note: Using synthetic data for initial development.")
        print("Real datasets require authentication/download from:")
        print("- PhysioNet: https://physionet.org/")
        print("- UCI ML Repository: https://archive.ics.uci.edu/")
        print("- WESAD: https://ubicomp.eti.uni-siegen.de/")

    def create_synthetic_dataset(
        self,
        n_samples: int = 10000,
        noise_level: float = 0.1
    ) -> pd.DataFrame:
        """
        Create synthetic alcohol sensor data for initial development
        Based on physiological models of alcohol effects

        Args:
            n_samples: Number of samples to generate
            noise_level: Amount of random noise to add

        Returns:
            DataFrame with synthetic sensor data and BAC labels
        """
        np.random.seed(42)

        # Generate time series (assuming 30-second intervals)
        timestamps = pd.date_range('2024-01-01', periods=n_samples, freq='30S')

        # Simulate BAC levels (g/dL) - typical drinking scenario
        # Absorption phase: 0-2 hours, Peak: 2-3 hours, Elimination: 3-8 hours
        time_hours = np.linspace(0, 8, n_samples)

        # Widmark formula-inspired BAC curve
        bac_true = np.zeros(n_samples)
        for i, t in enumerate(time_hours):
            if t < 2:  # Absorption
                bac_true[i] = 0.04 * t  # Rising to ~0.08
            elif t < 3:  # Peak
                bac_true[i] = 0.08 + 0.01 * np.sin((t-2) * np.pi)
            else:  # Elimination (0.015 g/dL per hour)
                bac_true[i] = max(0, 0.09 - 0.015 * (t - 3))

        # Add inter-individual variability
        bac_true += np.random.normal(0, 0.005, n_samples)
        bac_true = np.clip(bac_true, 0, 0.3)

        # Generate PPG (heart rate) - increases with alcohol
        # Baseline: 60-80 bpm, Increase: +10-30 bpm with alcohol
        hr_baseline = np.random.uniform(60, 80, n_samples)
        hr_increase = bac_true * 150  # Alcohol effect
        ppg_hr = hr_baseline + hr_increase + np.random.normal(0, 5, n_samples)

        # PPG signal quality (decreases slightly with high BAC due to vasodilation)
        ppg_quality = 0.95 - bac_true * 0.3 + np.random.normal(0, 0.05, n_samples)
        ppg_quality = np.clip(ppg_quality, 0.5, 1.0)

        # EDA (electrodermal activity) - increases with alcohol
        # Baseline: 2-10 µS, Increase with alcohol
        eda_baseline = np.random.uniform(2, 5, n_samples)
        eda_increase = bac_true * 20  # Alcohol effect
        eda_value = eda_baseline + eda_increase + np.random.normal(0, 0.5, n_samples)
        eda_value = np.clip(eda_value, 1, 20)

        # Skin temperature - increases slightly with alcohol (vasodilation)
        # Baseline: 32-34°C, Increase: +0.5-2°C
        temp_baseline = np.random.uniform(32, 34, n_samples)
        temp_increase = bac_true * 5
        temperature = temp_baseline + temp_increase + np.random.normal(0, 0.3, n_samples)

        # Environmental factors
        ambient_temp = np.random.uniform(20, 30, n_samples)  # Room temperature
        humidity = np.random.uniform(30, 70, n_samples)  # Humidity %

        # Add noise
        ppg_hr += np.random.normal(0, noise_level * 10, n_samples)
        eda_value += np.random.normal(0, noise_level, n_samples)
        temperature += np.random.normal(0, noise_level * 0.5, n_samples)

        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'ppg_heart_rate': ppg_hr,
            'ppg_quality': ppg_quality,
            'eda_value': eda_value,
            'skin_temperature': temperature,
            'ambient_temperature': ambient_temp,
            'humidity': humidity,
            'bac_true': bac_true,
            'subject_id': np.random.randint(1, 50, n_samples),  # 50 subjects
            'session_id': np.random.randint(1, 100, n_samples)
        })

        return df

    def load_real_datasets(self) -> Optional[pd.DataFrame]:
        """
        Load real transdermal alcohol and physiological datasets
        This would integrate actual research data when available
        """
        # Placeholder for real dataset integration
        print("Real dataset loading not yet implemented.")
        print("Using synthetic data for initial development.")
        return None

    def preprocess_data(
        self,
        df: pd.DataFrame,
        normalize: bool = True,
        remove_outliers: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess sensor data for model training

        Args:
            df: Raw sensor data
            normalize: Whether to normalize features
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

        # Feature engineering
        df_clean['ppg_eda_ratio'] = df_clean['ppg_heart_rate'] / df_clean['eda_value']
        df_clean['temp_ambient_diff'] = (
            df_clean['skin_temperature'] - df_clean['ambient_temperature']
        )

        # Time-based features
        df_clean['hour'] = df_clean['timestamp'].dt.hour
        df_clean['minute'] = df_clean['timestamp'].dt.minute

        # Normalize if requested
        if normalize:
            from sklearn.preprocessing import StandardScaler

            feature_cols = [
                'ppg_heart_rate', 'ppg_quality', 'eda_value',
                'skin_temperature', 'ambient_temperature', 'humidity',
                'ppg_eda_ratio', 'temp_ambient_diff'
            ]

            scaler = StandardScaler()
            df_clean[feature_cols] = scaler.fit_transform(df_clean[feature_cols])

        return df_clean

    def create_sequences(
        self,
        df: pd.DataFrame,
        sequence_length: int = 10,
        target_col: str = 'bac_true'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time-series model training

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

        # Group by session to maintain temporal continuity
        for session_id in df['session_id'].unique():
            session_data = df[df['session_id'] == session_id].sort_values('timestamp')

            if len(session_data) < sequence_length:
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
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train, validation, and test sets
        """
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


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = AlcoholDatasetLoader()

    # Create synthetic dataset
    print("Creating synthetic dataset...")
    df = loader.create_synthetic_dataset(n_samples=10000)

    # Preprocess
    print("Preprocessing data...")
    df_processed = loader.preprocess_data(df)

    # Create sequences
    print("Creating sequences...")
    X, y = loader.create_sequences(df_processed, sequence_length=10)

    # Split data
    print("Splitting data...")
    X_train, X_val, X_test, y_train, y_val, y_test = loader.get_train_test_split(X, y)

    print(f"\nDataset Statistics:")
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Input shape: {X_train.shape}")
    print(f"BAC range: {y_train.min():.4f} - {y_train.max():.4f}")
