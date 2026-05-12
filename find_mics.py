from audio_core import get_input_devices


if __name__ == "__main__":
    for device in get_input_devices():
        print(f"[ID {device['id']}] {device['name']} | channels={device['channels']}")
