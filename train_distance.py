from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from audio_core import extract_distance_features_from_file, load_distance_training_rows


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "train" / "distance_multimic"
MODEL_PATH = BASE_DIR / "distance_estimator.pkl"


def train_single_mic_fallback():
    legacy_dir = BASE_DIR / "data" / "train" / "distances"
    if not legacy_dir.exists():
        raise FileNotFoundError("No distance training data found.")

    features = []
    labels = []
    for wav_path in sorted(legacy_dir.glob("*.wav")):
        name_parts = wav_path.stem.split("_")
        if len(name_parts) < 3:
            continue
        distance_cm = float(name_parts[1].replace("cm", ""))
        features.append(extract_distance_features_from_file(wav_path))
        labels.append(distance_cm)

    X = np.asarray(features, dtype=np.float32)
    y = np.asarray(labels, dtype=np.float32)
    return X, y, "single-mic"


def train_multimic():
    rows = load_distance_training_rows(DATA_DIR)
    if not rows:
        raise FileNotFoundError("No multi-mic calibration files found.")

    X = np.asarray([row["features"] for row in rows], dtype=np.float32)
    y = np.asarray([row["distance_cm"] for row in rows], dtype=np.float32)
    return X, y, "multimic"


def main():
    try:
        X, y, dataset_mode = train_multimic()
    except FileNotFoundError:
        X, y, dataset_mode = train_single_mic_fallback()

    unique_distances = sorted({float(value) for value in y.tolist()})

    test_size = 0.2 if len(X) >= 10 else 0.0
    if test_size > 0:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = RandomForestRegressor(n_estimators=250, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    bundle = {
        "model": model,
        "feature_mode": dataset_mode,
        "triangle_side_m": 1.0,
        "distance_label": "distance_from_centroid_cm" if dataset_mode == "multimic" else "distance_from_mic_cm",
        "feature_count": int(X.shape[1]),
        "mae_cm": float(mae),
        "trained_distances_cm": unique_distances,
    }
    joblib.dump(bundle, MODEL_PATH)

    print("Distance model trained.")
    print(f"Feature mode: {dataset_mode}")
    print(f"Samples: {len(X)}")
    print(f"Trained distances: {unique_distances}")
    print(f"Mean absolute error: {mae:.2f} cm")
    if len(unique_distances) <= 2:
        print("Warning: this model was trained on only a few distances, so distance estimates between or beyond them are rough.")
    print(f"Saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
