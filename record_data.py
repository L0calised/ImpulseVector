from __future__ import annotations

from pathlib import Path

import sounddevice as sd
from scipy.io.wavfile import write
from config import (
    AMBIENT_SAMPLE_COUNT,
    GUNSHOT_SAMPLE_COUNT,
    GUNSHOT_SAMPLE_DURATION,
    SAMPLE_RATE,
    SINGLE_TRAINING_MIC_ID,
)


BASE_DIR = Path(__file__).resolve().parent


def record_audio(category: str, filename: str, duration: float, sample_rate: int, device_id: int):
    target_dir = BASE_DIR / "data" / "train" / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{filename}.wav"

    print(f"Recording {category} sample to {target_path}")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        device=device_id,
        dtype="int16",
    )
    sd.wait()
    write(str(target_path), sample_rate, recording)
    print("Saved.")


def main():
    print("Recording gunshot and ambient training samples")
    print(f"Using microphone id: {SINGLE_TRAINING_MIC_ID}")
    print(f"Sample rate: {SAMPLE_RATE}")
    print(f"Duration per clip: {GUNSHOT_SAMPLE_DURATION} seconds")

    for index in range(1, GUNSHOT_SAMPLE_COUNT + 1):
        input(f"Press Enter to record gunshot sample {index}/{GUNSHOT_SAMPLE_COUNT} (clap loudly)...")
        record_audio(
            "gunshot",
            f"shot_{index}",
            GUNSHOT_SAMPLE_DURATION,
            SAMPLE_RATE,
            SINGLE_TRAINING_MIC_ID,
        )

    for index in range(1, AMBIENT_SAMPLE_COUNT + 1):
        input(f"Press Enter to record ambient sample {index}/{AMBIENT_SAMPLE_COUNT} (stay quiet)...")
        record_audio(
            "ambient",
            f"noise_{index}",
            GUNSHOT_SAMPLE_DURATION,
            SAMPLE_RATE,
            SINGLE_TRAINING_MIC_ID,
        )


if __name__ == "__main__":
    main()
