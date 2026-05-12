from __future__ import annotations

import concurrent.futures
import json
import math
from pathlib import Path

import joblib
import librosa
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write


MIC_POSITIONS_M = {
    "mic1": np.array([0.0, math.sqrt(3) / 3], dtype=np.float32),
    "mic2": np.array([-0.5, -math.sqrt(3) / 6], dtype=np.float32),
    "mic3": np.array([0.5, -math.sqrt(3) / 6], dtype=np.float32),
}
MIC_UI_POSITIONS = {
    "mic1": {"x_percent": 50.0, "y_percent": 20.0},
    "mic2": {"x_percent": 24.0, "y_percent": 72.0},
    "mic3": {"x_percent": 76.0, "y_percent": 72.0},
}


def get_input_devices():
    devices = []
    for index, device in enumerate(sd.query_devices()):
        if int(device["max_input_channels"]) > 0:
            devices.append(
                {
                    "id": index,
                    "name": device["name"],
                    "channels": int(device["max_input_channels"]),
                }
            )
    return devices


def load_classifier_model(model_path: Path):
    return joblib.load(model_path) if model_path.exists() else None


def load_level_calibration(calibration_path: Path):
    if not calibration_path.exists():
        return None
    try:
        return json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_level_calibration(calibration_path: Path, profile: dict):
    calibration_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def _to_mono_float(audio: np.ndarray) -> np.ndarray:
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return audio.astype(np.float32).flatten()


def record_single_mic(device_id: int, duration: float, sample_rate: int):
    device_info = sd.query_devices(device_id)
    channels = max(1, int(device_info["max_input_channels"]))
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        device=device_id,
        dtype="int16",
    )
    sd.wait()
    audio_int16 = recording.copy()
    audio_float = _to_mono_float(recording) / 32768.0
    return audio_float, audio_int16


def record_from_three_mics(
    mic_ids: list[int],
    duration: float,
    sample_rate: int,
    debug_dir: Path | None = None,
):
    names = ["mic1", "mic2", "mic3"]
    captures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            name: pool.submit(record_single_mic, device_id, duration, sample_rate)
            for name, device_id in zip(names, mic_ids)
        }
        for name, future in futures.items():
            audio_float, audio_int16 = future.result()
            captures[name] = {"float": audio_float, "int16": audio_int16}

    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        for name, payload in captures.items():
            write(str(debug_dir / f"{name}.wav"), sample_rate, payload["int16"])

    return captures


def trim_to_event(audio: np.ndarray, threshold: float = 0.2, window: int = 4096) -> np.ndarray:
    envelope = np.abs(audio)
    if envelope.size == 0:
        return audio
    peak_index = int(np.argmax(envelope))
    start = max(0, peak_index - window)
    end = min(len(audio), peak_index + window)
    clip = audio[start:end]
    if np.max(np.abs(clip)) < threshold:
        return audio
    return clip


def extract_classifier_features(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    audio = trim_to_event(audio, threshold=0.05, window=8192)
    mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=20)
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)
    zero_crossing = librosa.feature.zero_crossing_rate(audio)
    rms = librosa.feature.rms(y=audio)
    return np.concatenate(
        [
            np.mean(mfcc, axis=1),
            np.std(mfcc, axis=1),
            np.mean(spectral_centroid, axis=1),
            np.mean(zero_crossing, axis=1),
            np.mean(rms, axis=1),
        ]
    ).astype(np.float32)


def extract_classifier_features_from_file(path: Path) -> np.ndarray:
    audio, sample_rate = librosa.load(path, sr=None, mono=True)
    return extract_classifier_features(audio, sample_rate)


def build_level_calibration_profile(
    captures: dict[str, dict[str, np.ndarray]],
    mic_ids: list[int],
) -> dict[str, object]:
    metrics = _summarize_capture_strength(captures)
    rms_values = [max(metrics[name]["rms"], 1e-6) for name in ("mic1", "mic2", "mic3")]
    target_rms = float(np.mean(rms_values))
    gains = {
        name: float(np.clip(target_rms / max(metrics[name]["rms"], 1e-6), 0.25, 4.0))
        for name in ("mic1", "mic2", "mic3")
    }
    return {
        "mic_ids": [int(mic_id) for mic_id in mic_ids],
        "target_rms": target_rms,
        "gains": gains,
        "measured_rms": {name: float(metrics[name]["rms"]) for name in ("mic1", "mic2", "mic3")},
    }


def _get_level_gain(
    calibration_profile: dict[str, object] | None,
    mic_name: str,
    mic_ids: list[int] | None,
) -> float:
    if calibration_profile is None:
        return 1.0
    profile_mic_ids = calibration_profile.get("mic_ids")
    if mic_ids is not None and profile_mic_ids != [int(mic_id) for mic_id in mic_ids]:
        return 1.0
    gains = calibration_profile.get("gains", {})
    gain = gains.get(mic_name, 1.0) if isinstance(gains, dict) else 1.0
    return float(gain)


def _summarize_capture_strength(captures: dict[str, dict[str, np.ndarray]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for mic_name, payload in captures.items():
        audio = trim_to_event(payload["float"], threshold=0.03, window=4096)
        abs_audio = np.abs(audio)
        peak = float(np.max(abs_audio)) if abs_audio.size else 0.0
        rms = float(np.sqrt(np.mean(audio**2) + 1e-12)) if audio.size else 0.0
        peak_index = int(np.argmax(abs_audio)) if abs_audio.size else 0
        summary[mic_name] = {"peak": peak, "rms": rms, "peak_index": peak_index}
    return summary


def _weighted_ui_pin(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 1e-9:
        return {"x_percent": 50.0, "y_percent": 50.0}

    x = 0.0
    y = 0.0
    for mic_name, weight in weights.items():
        x += MIC_UI_POSITIONS[mic_name]["x_percent"] * weight
        y += MIC_UI_POSITIONS[mic_name]["y_percent"] * weight
    return {"x_percent": round(x / total, 2), "y_percent": round(y / total, 2)}


def _dominant_ui_pin(mic_name: str, dominance: float) -> dict[str, float]:
    center_x = 50.0
    center_y = 50.0
    mic_x = MIC_UI_POSITIONS[mic_name]["x_percent"]
    mic_y = MIC_UI_POSITIONS[mic_name]["y_percent"]
    blend = float(np.clip((dominance - 0.34) / 0.33, 0.25, 0.95))
    return {
        "x_percent": round(center_x + (mic_x - center_x) * blend, 2),
        "y_percent": round(center_y + (mic_y - center_y) * blend, 2),
    }


def estimate_direction_hint(
    captures: dict[str, dict[str, np.ndarray]],
    sample_rate: int = 44100,
    calibration_profile: dict[str, object] | None = None,
    mic_ids: list[int] | None = None,
):
    metrics = _summarize_capture_strength(captures)
    for mic_name, item in metrics.items():
        gain = _get_level_gain(calibration_profile, mic_name, mic_ids)
        item["peak"] *= gain
        item["rms"] *= gain

    ranked = sorted(metrics.items(), key=lambda item: item[1]["rms"], reverse=True)
    top_name, top_metrics = ranked[0]
    second_name, second_metrics = ranked[1]
    third_name, third_metrics = ranked[2]

    total_rms = sum(item["rms"] for item in metrics.values())
    dominance = top_metrics["rms"] / (total_rms + 1e-9)
    separation = top_metrics["rms"] - second_metrics["rms"]
    separation_ratio = separation / (top_metrics["rms"] + 1e-9)

    left_energy = metrics["mic2"]["rms"]
    right_energy = metrics["mic3"]["rms"]
    front_energy = metrics["mic1"]["rms"]

    timing_span = max(item["peak_index"] for item in metrics.values()) - min(
        item["peak_index"] for item in metrics.values()
    )
    timing_conflict = timing_span > 0.012 * sample_rate

    direction_label = "uncertain"
    angle_deg = None
    approx_location = None

    if dominance >= 0.5 and separation_ratio >= 0.18 and not timing_conflict:
        if top_name == "mic1":
            direction_label = "front"
            angle_deg = 90.0
            approx_location = "near mic 1 side"
        elif top_name == "mic2":
            direction_label = "left"
            angle_deg = 210.0
            approx_location = "near mic 2 side"
        else:
            direction_label = "right"
            angle_deg = 330.0
            approx_location = "near mic 3 side"
    elif abs(left_energy - right_energy) <= 0.08 * max(left_energy, right_energy, 1e-9):
        if front_energy > max(left_energy, right_energy) * 1.12:
            direction_label = "front"
            angle_deg = 90.0
            approx_location = "in front of the array"
        else:
            direction_label = "rear"
            angle_deg = 270.0
            approx_location = "behind the array, between mic 2 and mic 3"
    elif left_energy > right_energy * 1.15:
        direction_label = "front-left" if front_energy > left_energy * 0.9 else "left"
        angle_deg = 150.0 if direction_label == "front-left" else 210.0
        approx_location = "between mic 1 and mic 2" if direction_label == "front-left" else "left of the array"
    elif right_energy > left_energy * 1.15:
        direction_label = "front-right" if front_energy > right_energy * 0.9 else "right"
        angle_deg = 30.0 if direction_label == "front-right" else 330.0
        approx_location = "between mic 1 and mic 3" if direction_label == "front-right" else "right of the array"

    certainty = "low"
    if direction_label != "uncertain":
        if dominance >= 0.58 and separation_ratio >= 0.25 and not timing_conflict:
            certainty = "high"
        elif dominance >= 0.45 and separation_ratio >= 0.12:
            certainty = "medium"

    if dominance >= 0.45:
        pin = _dominant_ui_pin(top_name, dominance)
    else:
        pin = _weighted_ui_pin({name: max(item["rms"], 1e-6) for name, item in metrics.items()})

    if certainty == "low":
        approx_location = None if direction_label == "uncertain" else approx_location

    return {
        "direction_label": direction_label,
        "angle_deg": angle_deg,
        "certainty": certainty,
        "approx_location": approx_location,
        "pin": pin,
        "timing_conflict": timing_conflict,
        "dominant_mic": top_name,
        "dominance": dominance,
        "second_mic": second_name,
        "third_mic": third_name,
        "calibration_gains": None
        if calibration_profile is None
        else {
            name: round(_get_level_gain(calibration_profile, name, mic_ids), 3)
            for name in ("mic1", "mic2", "mic3")
        },
    }


def detect_gunshot_from_capture(
    captures,
    classifier_bundle,
    sample_rate: int = 44100,
    calibration_profile: dict[str, object] | None = None,
    mic_ids: list[int] | None = None,
):
    classifier_features = extract_classifier_features(captures["mic1"]["float"], sample_rate).reshape(1, -1)

    if classifier_bundle is None:
        is_gunshot = True
        confidence = None
    else:
        model = classifier_bundle["model"]
        predicted = int(model.predict(classifier_features)[0])
        is_gunshot = predicted == 1
        if hasattr(model, "predict_proba"):
            confidence = float(model.predict_proba(classifier_features)[0][predicted])
        else:
            confidence = None

    direction = estimate_direction_hint(
        captures,
        sample_rate,
        calibration_profile=calibration_profile,
        mic_ids=mic_ids,
    )
    max_level = max(float(np.max(np.abs(captures[name]["float"]))) for name in captures)

    return {
        "is_gunshot": is_gunshot,
        "confidence": confidence,
        "direction": direction,
        "max_level": max_level,
    }


def build_detection_summary(result):
    direction = result["direction"]
    if direction["direction_label"] == "uncertain":
        message = "Sound detected, but source direction is uncertain with the current USB mic timing."
    elif result["is_gunshot"]:
        message = f"Possible gunshot detected from the {direction['direction_label']}."
    else:
        message = f"Sound detected from the {direction['direction_label']}, classified as non-gunshot."

    return {
        "status": "alert" if result["is_gunshot"] else "clear",
        "message": message,
        "confidence": result["confidence"],
        "direction_label": direction["direction_label"],
        "angle_deg": direction["angle_deg"],
        "approx_location": direction["approx_location"],
        "direction_certainty": direction["certainty"],
        "dominant_mic": direction["dominant_mic"],
        "pin": direction["pin"],
        "signal_level": result["max_level"],
        "calibration_gains": result["direction"].get("calibration_gains"),
        "calibration_note": "Direction is estimated from relative mic strength only. Separate USB mic timing can make the result uncertain.",
    }
