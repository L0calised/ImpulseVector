import os
import numpy as np
import librosa
import tensorflow as tf
import logging

# Load the trained brain once when the server starts
print("[AI] Loading Model...")
try:
    model = tf.keras.models.load_model("gunshot_brain.h5")
    print("[AI] Model Loaded Successfully!")
except:
    print("[AI] WARNING: 'gunshot_brain.h5' not found. Run train_model.py first!")
    model = None

CLASSES = ["noise", "gunshots"]
SAMPLE_RATE = 22050
DURATION = 2

def extract_features(file_path):
    """Same feature extraction as training"""
    try:
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
        if len(audio) < SAMPLE_RATE * DURATION:
            audio = np.pad(audio, (0, int(SAMPLE_RATE * DURATION - len(audio))), 'constant')
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        return np.mean(mfccs.T, axis=0)
    except Exception as e:
        print(f"Error reading audio: {e}")
        return None

def analyze_audio(file_path):
    """
    Input: Path to a .wav file
    Output: Real prediction from Neural Network
    """
    print(f"[AI] Analyzing {file_path}...")

    if model is None:
        return {"is_gunshot": False, "confidence": 0, "class": "Error: No Model"}

    # 1. Prepare Audio
    features = extract_features(file_path)
    if features is None:
        return {"is_gunshot": False, "confidence": 0, "class": "Error: Bad Audio"}

    # 2. Reshape for Model (1 sample, 40 features)
    features = np.expand_dims(features, axis=0)

    # 3. Predict
    prediction = model.predict(features) # Returns [[Prob_Noise, Prob_Gun]]
    confidence_gun = prediction[0][1]
    confidence_noise = prediction[0][0]

    # 4. Decide
    is_gunshot = confidence_gun > 0.60 # Threshold (60% sure)

    result = {
        "is_gunshot": bool(is_gunshot),
        "confidence": round(float(confidence_gun) * 100, 2),
        "class": "Gunshot" if is_gunshot else "Noise/Other"
    }

    print(f"[AI] Result: {result['class']} ({result['confidence']}%)")

    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)

    return result
