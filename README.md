# Triangulation Hunt

Student prototype for detecting a loud event with 3 USB microphones, classifying whether it sounds like a gunshot, and showing a coarse source-direction hint on a small web dashboard.

## Simplest setup

Edit only [config.py](/C:/Users/divya/Documents/Triangulation_Hunt/config.py), then run the Python files directly.

## What this prototype does

- Lets you choose 3 microphones from a website
- Records from all 3 microphones for one listening window
- Runs a simple gunshot-vs-ambient classifier
- Uses relative mic strength to estimate a coarse direction
- Shows an alert and an approximate strongest-side pin on the dashboard

## Project layout

- `app.py`: Flask + Socket.IO dashboard backend
- `audio_core.py`: recording, features, detection, distance estimation helpers
- `record_data.py`: record ambient and clap-based gunshot-like samples
- `record_distance.py`: record the 50-clap 3-mic calibration dataset
- `train_model.py`: train gunshot classifier
- `find_mics.py`: list input device ids
- `templates/index.html`: dashboard UI

## Recommended setup

- Language: Python 3.11
- IDE: VS Code
- OS: Windows is fine for this prototype

## Step 1: create the environment

Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Step 2: find your microphone ids

Run:

```powershell
python find_mics.py
```

Write down the ids for the 3 USB microphones you want to use.

Then open [config.py](/C:/Users/divya/Documents/Triangulation_Hunt/config.py) and set:

```python
SINGLE_TRAINING_MIC_ID = 1
ARRAY_MIC_IDS = [1, 2, 3]
```

## Step 3: record gunshot-like and ambient samples

For a student prototype, using loud hand claps as the positive class is acceptable.

Run:

```powershell
python record_data.py
```

This creates:

- `data/train/gunshot`
- `data/train/ambient`

## Step 4: train the model

Train the classifier:

```powershell
python train_model.py
```

Models saved:

- `gunshot_classifier.pkl`

## Step 5: run the website

Start the server:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Step 6: test integration

1. Open the website
2. Select the 3 microphones
3. Click `Start Listening`
4. Make a clap or play a test sound
5. Check whether the website shows:
   - classification result
   - coarse direction
   - approximate strongest-side pin

Debug recordings are saved in:

- `debug/mic1.wav`
- `debug/mic2.wav`
- `debug/mic3.wav`

Use this plotter if needed:

```powershell
python test_plotter.py
```

## Important prototype limits

- Three separate USB microphones on one laptop are not perfectly synchronized
- Real gunshot detection needs much more data than hand claps
- The direction hint is coarse and may be uncertain
- Approximate location is only a strongest-side hint, not real triangulation

## How direction works here

The dashboard compares relative signal strength across the three microphones and reports a coarse direction such as `front`, `left`, `right`, `front-left`, or `front-right`. Because the microphones are separate USB devices, timing between them is not reliable enough for true triangulation.

## Final run order

```powershell
python find_mics.py
python record_data.py
python train_model.py
python app.py
```
