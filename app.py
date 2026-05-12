from __future__ import annotations

from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from audio_core import (
    build_detection_summary,
    build_level_calibration_profile,
    detect_gunshot_from_capture,
    get_input_devices,
    load_classifier_model,
    load_level_calibration,
    record_from_three_mics,
    save_level_calibration,
)
from config import ARRAY_MIC_IDS, LIVE_CAPTURE_DURATION, SAMPLE_RATE, WEB_PORT


BASE_DIR = Path(__file__).resolve().parent
CALIBRATION_PATH = BASE_DIR / "mic_level_calibration.json"
app = Flask(__name__)
app.config["SECRET_KEY"] = "triangulation-hunt"
socketio = SocketIO(app, cors_allowed_origins="*")

classifier_bundle = load_classifier_model(BASE_DIR / "gunshot_classifier.pkl")
level_calibration = load_level_calibration(CALIBRATION_PATH)

state = {
    "armed": False,
    "calibrating": False,
}
state_lock = Lock()


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "classifier_loaded": classifier_bundle is not None,
            "armed": state["armed"],
            "calibrating": state["calibrating"],
            "default_mics": ARRAY_MIC_IDS,
            "default_duration": LIVE_CAPTURE_DURATION,
            "level_calibration": level_calibration,
        }
    )


@app.get("/get_mics")
def get_mics():
    return jsonify(get_input_devices())


@app.post("/start_listening")
def start_listening():
    payload = request.get_json(force=True)
    mic_ids = [
        int(payload.get("mic1", ARRAY_MIC_IDS[0])),
        int(payload.get("mic2", ARRAY_MIC_IDS[1])),
        int(payload.get("mic3", ARRAY_MIC_IDS[2])),
    ]
    sample_rate = int(payload.get("sample_rate", SAMPLE_RATE))
    duration = float(payload.get("duration", LIVE_CAPTURE_DURATION))

    with state_lock:
        if state["armed"]:
            return jsonify({"error": "System is already listening."}), 409
        if state["calibrating"]:
            return jsonify({"error": "Calibration is already running."}), 409
        state["armed"] = True

    socketio.start_background_task(
        target=run_detection_cycle,
        mic_ids=mic_ids,
        sample_rate=sample_rate,
        duration=duration,
    )
    return jsonify({"status": "Listening cycle started."})


@app.post("/calibrate_mics")
def calibrate_mics():
    payload = request.get_json(force=True)
    mic_ids = [
        int(payload.get("mic1", ARRAY_MIC_IDS[0])),
        int(payload.get("mic2", ARRAY_MIC_IDS[1])),
        int(payload.get("mic3", ARRAY_MIC_IDS[2])),
    ]
    sample_rate = int(payload.get("sample_rate", SAMPLE_RATE))
    duration = float(payload.get("duration", LIVE_CAPTURE_DURATION))

    with state_lock:
        if state["armed"]:
            return jsonify({"error": "System is already listening."}), 409
        if state["calibrating"]:
            return jsonify({"error": "Calibration is already running."}), 409
        state["calibrating"] = True

    socketio.start_background_task(
        target=run_calibration_cycle,
        mic_ids=mic_ids,
        sample_rate=sample_rate,
        duration=duration,
    )
    return jsonify({"status": "Calibration started."})


@app.post("/stop_listening")
def stop_listening():
    with state_lock:
        state["armed"] = False
        state["calibrating"] = False
    socketio.emit("listening_stopped")
    return jsonify({"status": "Listening stopped."})


def run_detection_cycle(mic_ids: list[int], sample_rate: int, duration: float):
    try:
        captures = record_from_three_mics(
            mic_ids=mic_ids,
            duration=duration,
            sample_rate=sample_rate,
            debug_dir=BASE_DIR / "debug",
        )

        with state_lock:
            if not state["armed"]:
                return

        result = detect_gunshot_from_capture(
            captures=captures,
            classifier_bundle=classifier_bundle,
            calibration_profile=level_calibration,
            mic_ids=mic_ids,
        )

        summary = build_detection_summary(result)
        socketio.emit("analysis_result", summary)

        if result["is_gunshot"]:
            socketio.emit("gunshot_alert", summary)
    except Exception as exc:
        socketio.emit("analysis_result", {"status": "error", "message": str(exc)})
    finally:
        with state_lock:
            state["armed"] = False
        socketio.emit("listening_stopped")


def run_calibration_cycle(mic_ids: list[int], sample_rate: int, duration: float):
    global level_calibration

    try:
        captures = record_from_three_mics(
            mic_ids=mic_ids,
            duration=duration,
            sample_rate=sample_rate,
            debug_dir=BASE_DIR / "debug",
        )
        profile = build_level_calibration_profile(captures=captures, mic_ids=mic_ids)
        level_calibration = profile
        save_level_calibration(CALIBRATION_PATH, profile)
        socketio.emit(
            "calibration_result",
            {
                "status": "ok",
                "message": "Calibration saved. Use a center clap as the reference and keep mic positions fixed.",
                "level_calibration": profile,
            },
        )
    except Exception as exc:
        socketio.emit("calibration_result", {"status": "error", "message": str(exc)})
    finally:
        with state_lock:
            state["calibrating"] = False
        socketio.emit("listening_stopped")


if __name__ == "__main__":
    socketio.run(app, debug=True, port=WEB_PORT)
