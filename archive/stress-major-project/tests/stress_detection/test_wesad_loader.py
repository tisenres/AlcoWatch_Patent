import pickle
import numpy as np
import pytest
from stress_detection.data.wesad_loader import WESADLoader


def make_fake_pkl(tmp_path, subject='S2'):
    """Minimal WESAD .pkl structure (1 minute of data)."""
    n_bvp = 64 * 60    # 1 min at 64 Hz
    n_eda = 4 * 60     # 1 min at 4 Hz
    n_acc = 32 * 60    # 1 min at 32 Hz
    n_label = 700 * 60 # 1 min at 700 Hz
    data = {
        'signal': {
            'wrist': {
                'BVP':  np.random.randn(n_bvp, 1).astype(np.float32),
                'EDA':  np.random.randn(n_eda, 1).astype(np.float32),
                'TEMP': np.random.randn(n_eda, 1).astype(np.float32),
                'ACC':  np.random.randn(n_acc, 3).astype(np.float32),
            }
        },
        'label': np.random.randint(0, 5, n_label).astype(np.int32),
        'subject': subject,
    }
    subdir = tmp_path / subject
    subdir.mkdir()
    pkl_path = subdir / f"{subject}.pkl"
    with open(pkl_path, 'wb') as f:
        pickle.dump(data, f)
    return str(pkl_path)


class TestWESADLoader:
    def test_load_subject_returns_expected_keys(self, tmp_path):
        pkl_path = make_fake_pkl(tmp_path)
        loader = WESADLoader(data_dir=str(tmp_path))
        result = loader.load_subject('S2', pkl_path=pkl_path)
        for key in ('BVP', 'EDA', 'TEMP', 'ACC', 'labels', 'subject'):
            assert key in result

    def test_signals_are_1d(self, tmp_path):
        pkl_path = make_fake_pkl(tmp_path)
        loader = WESADLoader(data_dir=str(tmp_path))
        result = loader.load_subject('S2', pkl_path=pkl_path)
        assert result['BVP'].ndim == 1
        assert result['EDA'].ndim == 1
        assert result['TEMP'].ndim == 1
        assert result['ACC'].ndim == 1  # ACC magnitude

    def test_acc_is_magnitude_not_3axis(self, tmp_path):
        pkl_path = make_fake_pkl(tmp_path)
        loader = WESADLoader(data_dir=str(tmp_path))
        result = loader.load_subject('S2', pkl_path=pkl_path)
        assert result['ACC'].ndim == 1
        assert np.all(result['ACC'] >= 0)  # magnitude is non-negative

    def test_available_subjects_scans_directory(self, tmp_path):
        for s in ['S2', 'S5', 'S11']:
            make_fake_pkl(tmp_path, subject=s)
        loader = WESADLoader(data_dir=str(tmp_path))
        assert set(loader.available_subjects()) == {'S2', 'S5', 'S11'}
