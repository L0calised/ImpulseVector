import os
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical

# Config
DATA_PATH = "training_data"
CLASSES = ["noise", "gunshots"] # 0 = noise, 1 = gunshot
SAMPLE_RATE = 22050
DURATION = 2 # Seconds to analyze

def extract_features(file_path):
    """Converts audio to a Mel-Spectrogram (image-like data)"""
    try:
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
        # Pad audio if it's too short
        if len(audio) < SAMPLE_RATE * DURATION:
            audio = np.pad(audio, (0, int(SAMPLE_RATE * DURATION - len(audio))), 'constant')

        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        return np.mean(mfccs.T, axis=0)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

# 1. Load Data
X = [] # Features
y = [] # Labels (0 or 1)

print("--- Loading Audio Files ---")
for label_id, label_name in enumerate(CLASSES):
    folder = os.path.join(DATA_PATH, label_name)
    if not os.path.exists(folder):
        print(f"WARNING: Folder {folder} not found! Create it and add .wav files.")
        continue

    for file in os.listdir(folder):
        if file.endswith(".wav"):
            path = os.path.join(folder, file)
            features = extract_features(path)
            if features is not None:
                X.append(features)
                y.append(label_id)
                print(f"Loaded: {file} ({label_name})")

X = np.array(X)
y = np.array(y)

# Check if we have enough data
if len(X) < 2:
    print("ERROR: Not enough data to train! Add at least 1 file to each folder.")
    exit()

# 2. Prepare for Training
y = to_categorical(y, num_classes=2)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Build the Brain (Neural Network)
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(256, activation='relu', input_shape=(40,)),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(2, activation='softmax') # Output: [Prob_Noise, Prob_Gun]
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 4. Train
print("\n--- Training Model ---")
model.fit(X_train, y_train, epochs=50, batch_size=4, validation_data=(X_test, y_test))

# 5. Save
model.save("gunshot_brain.h5")
print("\n[SUCCESS] Model saved as 'gunshot_brain.h5'")
