# ImpulseVector 🎯
**Real-Time Acoustic Triangulation & Machine Learning System for Anti-Poaching**

ImpulseVector is a hybrid hardware and software system designed to instantly locate and verify illegal hunting activity in protected areas. By combining low-latency microphone arrays, Time Difference of Arrival (TDOA) physics, and Convolutional Neural Networks (CNNs), the system pinpoints the origin of a loud impulse and instantly verifies whether the sound was a legitimate gunshot or a false alarm (e.g., dog bark, vehicle, or jackhammer).

## 📌 System Architecture

The project is divided into three core layers:

1. **The Reflex (Hardware & C++):** A 3-microphone array deployed in an equilateral triangle. C++ handles ultra-low latency audio capture. When an acoustic impulse is detected, it calculates TDOA to triangulate the exact `(x, y)` coordinates and saves the audio snippet as a raw `.wav` file.
2. **The Brain (Python & Machine Learning):** A highly trained CNN built with TensorFlow and Keras. The `watchdog.py` script monitors incoming audio, converts it into Mel-frequency cepstral coefficients (MFCCs) using Librosa, and outputs a confidence score to filter out "Hard Negatives" (sounds that mimic gunshots).
3. **The Face (Web Dashboard):** A Python Flask backend coupled with an HTML5 `<canvas>` frontend. It receives real-time WebSocket alerts and instantly plots the triangulated gunshot on a visual radar grid.

## 📂 Project Structure

```text
/ImpulseVector
├── /audio_data               # Training datasets
│   ├── /gunshots             # Positive data (Class 6)
│   └── /others               # Hard negative data (Dogs, drills, etc.)
├── /incoming_audio           # Inbox for C++ to drop live .wav captures
├── /web_dashboard            # Flask server and UI
│   ├── app.py                # Web backend and WebSocket emitter
│   └── /templates
│       └── index.html        # Real-time radar UI
├── gunshot_brain.h5          # Compiled Keras AI Model
├── sort_files.py             # Preps UrbanSound8K dataset (Hard Negative Mining)
├── train_model.py            # CNN architecture and training logic
└── watchdog.py               # 24/7 monitor bridging C++ and the Web UI


⚙️ Setup & Installation
Prerequisites:
Python 3.8+
Visual Studio Code (Recommended
Git

1. Clone the Repository:
git clone [https://github.com/L0calised/ImpulseVector.git](https://github.com/L0calised/ImpulseVector.git)
cd ImpulseVector
2. Install Python Dependencies:
pip install numpy librosa tensorflow scikit-learn flask flask-socketio requests resampy
3. Running the Prototype
To test the software stack locally, you need two terminal windows running simultaneously.

Terminal 1: Start the Web Dashboard
python web_dashboard/app.py
Open your browser and navigate to http://localhost:5000 to view the radar grid.

Terminal 2: Start the AI Watchdog
python watchdog.py
The watchdog is now monitoring the /incoming_audio folder.

Simulate a Gunshot:
Drag and drop a raw .wav audio file (containing a gunshot) into the /incoming_audio folder. The Watchdog will analyze it, and if the confidence score exceeds the threshold, the web dashboard will instantly flash red and plot the coordinates.

Dataset used for training the model
Download the UrbanSound8K Dataset.
