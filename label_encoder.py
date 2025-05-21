## src/inference/label_encoder.py

import joblib
import numpy as np
from typing import List, Union
from sklearn.preprocessing import LabelEncoder

class PrivacyCaseLabelEncoder:
    def __init__(self, version: str):
        self.version = version
        self.encoder = LabelEncoder()

    def fit(self, labels: List[Union[str, int]]) -> np.ndarray:
        return self.encoder.fit_transform(labels)

    def transform(self, labels: List[Union[str, int]]) -> np.ndarray:
        return self.encoder.transform(labels)

    def inverse_transform(self, encoded: List[int]) -> List[str]:
        return self.encoder.inverse_transform(encoded)

    def save(self, path: str) -> None:
        metadata = {
            'version': self.version,
            'classes_': list(self.encoder.classes_)
        }
        joblib.dump((self.encoder, metadata), path)

    @classmethod
    def load(cls, path: str):
        encoder, metadata = joblib.load(path)
        instance = cls(version=metadata.get("version", "unknown"))
        instance.encoder = encoder
        return instance

    def get_metadata(self) -> dict:
        return {
            'version': self.version,
            'classes': list(self.encoder.classes_)
        }

    def encode_schema(self) -> dict:
        return {
            'type': 'integer',
            'description': f'Encoded label using LabelEncoder v{self.version}',
            'enum': list(map(int, range(len(self.encoder.classes_)))),
            'classes': list(self.encoder.classes_)
        }
