import os
import json
import time
import threading
from flask import Flask, render_template, request, jsonify
from ml_engine import analyze_audio  # Import our new AI module

app = Flask(__name__)

# Files shared with C++
DEVICES_FILE = "available_devices.txt"
CONFIG_FILE = "config.txt"
DATA_FILE = "live_data.json"
AUDIO_FILE = "event_audio.wav"

# Global variable to store the FINAL result after AI checks it
current_event = {"status": "waiting"}

def monitor_system():
    """Background thread that watches for new C++ events"""
    global current_event
    last_timestamp = 0

    print("--- Background Monitor Started ---")
    while True:
        # Check if C++ has written a new event
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)

                # If this is a new event we haven't processed yet
                if data.get('timestamp') != last_timestamp and data.get('status') == 'analyzing':
                    print(f"\n[Server] New Event detected at {data['timestamp']}")
                    last_timestamp = data['timestamp']

                    # Update Web UI to say "Analyzing..."
                    current_event = data

                    # Wait for audio file to be ready (simulated buffer delay)
                    time.sleep(0.5)

                    if os.path.exists(AUDIO_FILE):
                        # CALL THE AI ENGINE
                        ai_result = analyze_audio(AUDIO_FILE)

                        # Merge AI results into the event data
                        current_event.update(ai_result)
                        current_event['status'] = 'confirmed' if ai_result['is_gunshot'] else 'rejected'

                        # Save back to JSON (optional, but good for logs)
                        # In a real app, you'd save to a database here.
                    else:
                        print("[Error] Audio file missing!")

            except Exception as e:
                print(f"Error reading data: {e}")

        time.sleep(0.5)

# Start the background monitor
monitor_thread = threading.Thread(target=monitor_system, daemon=True)
monitor_thread.start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/get_devices')
def get_devices():
    devices = []
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r') as f:
            for line in f:
                if ':' in line:
                    parts = line.strip().split(':', 1)
                    devices.append({'id': parts[0], 'name': parts[1]})
    return jsonify(devices)

@app.route('/save_config', methods=['POST'])
def save_config():
    data = request.json
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"MIC_A={data['mic_a']}\n")
            f.write(f"MIC_B={data['mic_b']}\n")
            f.write(f"MIC_C={data['mic_c']}\n")
        return jsonify({"status": "success", "message": "Config saved!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_live_data')
def get_live_data():
    """Returns the processed event to the website"""
    return jsonify(current_event)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
