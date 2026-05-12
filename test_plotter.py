from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile


BASE_DIR = Path(__file__).resolve().parent
DEBUG_DIR = BASE_DIR / "debug"


def main():
    files = [DEBUG_DIR / "mic1.wav", DEBUG_DIR / "mic2.wav", DEBUG_DIR / "mic3.wav"]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("Triangulation Hunt Debug Waveforms")

    for idx, path in enumerate(files):
        rate, data = wavfile.read(path)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        time_axis = np.linspace(0, len(data) / rate, num=len(data))
        axes[idx].plot(time_axis, data)
        axes[idx].set_ylabel(f"Mic {idx + 1}")

    axes[-1].set_xlabel("Seconds")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
