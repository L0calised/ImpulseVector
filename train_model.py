from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from audio_core import extract_classifier_features_from_file


BASE_DIR = Path(__file__).resolve().parent
TRAIN_DIR = BASE_DIR / "data" / "train"
MODEL_PATH = BASE_DIR / "gunshot_classifier.pkl"


def load_data():
    features = []
    labels = []
    class_map = {"ambient": 0, "gunshot": 1}

    for class_name, label in class_map.items():
        folder = TRAIN_DIR / class_name
        if not folder.exists():
            continue
        for wav_path in sorted(folder.glob("*.wav")):
            features.append(extract_classifier_features_from_file(wav_path))
            labels.append(label)

    return np.asarray(features, dtype=np.float32), np.asarray(labels, dtype=np.int32)


def main():
    X, y = load_data()
    if len(X) < 4:
        raise RuntimeError("Need more training audio in data/train/ambient and data/train/gunshot.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=250, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    bundle = {
        "model": model,
        "classes": {"ambient": 0, "gunshot": 1},
        "accuracy": float(accuracy),
    }
    joblib.dump(bundle, MODEL_PATH)

    print("Gunshot classifier trained.")
    print(f"Samples: {len(X)}")
    print(f"Accuracy: {accuracy * 100:.2f}%")
    print(classification_report(y_test, predictions, zero_division=0))
    print(f"Saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
