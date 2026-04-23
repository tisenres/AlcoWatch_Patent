import os
import pickle
from typing import Dict, List, Optional
import numpy as np


class WESADLoader:
    """Loads wrist sensor signals from WESAD .pkl files."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def available_subjects(self) -> List[str]:
        subjects = []
        for name in sorted(os.listdir(self.data_dir)):
            pkl = os.path.join(self.data_dir, name, f"{name}.pkl")
            if os.path.isfile(pkl):
                subjects.append(name)
        return subjects

    def load_subject(self, subject_id: str, pkl_path: Optional[str] = None) -> Dict:
        if pkl_path is None:
            pkl_path = os.path.join(self.data_dir, subject_id, f"{subject_id}.pkl")
        with open(pkl_path, 'rb') as f:
            raw = pickle.load(f, encoding='latin1')
        wrist = raw['signal']['wrist']
        return {
            'subject': subject_id,
            'BVP':    wrist['BVP'].flatten().astype(np.float32),
            'EDA':    wrist['EDA'].flatten().astype(np.float32),
            'TEMP':   wrist['TEMP'].flatten().astype(np.float32),
            'ACC':    np.linalg.norm(wrist['ACC'], axis=1).astype(np.float32),
            'labels': raw['label'].flatten().astype(np.int32),
        }
