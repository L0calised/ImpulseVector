from __future__ import annotations

from pathlib import Path

from scipy.io.wavfile import write

from audio_core import record_from_three_mics
from config import (
    ARRAY_MIC_IDS,
    DISTANCE_LABELS_CM,
    DISTANCE_SAMPLE_DURATION,
    DISTANCE_SAMPLES_PER_LABEL,
    SAMPLE_RATE,
)


BASE_DIR = Path(__file__).resolve().parent


def main():
    out_dir = BASE_DIR / "data" / "train" / "distance_multimic"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Calibration plan")
    print("Triangle layout: 3 microphones, 1 meter apart, equilateral triangle.")
    print("Label meaning: distance from triangle center to clap point.")
    print("Keep the clap angle roughly consistent for one full run if possible.")
    print(f"Microphone ids: {ARRAY_MIC_IDS}")
    print(f"Distances: {DISTANCE_LABELS_CM}")
    print(f"Samples per distance: {DISTANCE_SAMPLES_PER_LABEL}")

    mic_ids = ARRAY_MIC_IDS
    for distance_cm in DISTANCE_LABELS_CM:
        print(f"\nDistance {distance_cm} cm from array center")
        for sample_idx in range(1, DISTANCE_SAMPLES_PER_LABEL + 1):
            input(f"Press Enter for clap {sample_idx}/{DISTANCE_SAMPLES_PER_LABEL} at {distance_cm} cm...")
            captures = record_from_three_mics(
                mic_ids=mic_ids,
                duration=DISTANCE_SAMPLE_DURATION,
                sample_rate=SAMPLE_RATE,
            )
            for mic_name, audio in captures.items():
                filename = out_dir / f"clap_d{distance_cm:03d}_s{sample_idx:02d}_{mic_name}.wav"
                write(str(filename), SAMPLE_RATE, audio["int16"])
                print(f"Saved {filename.name}")

    print("\nFinished recording 3-mic distance calibration data.")


if __name__ == "__main__":
    main()
