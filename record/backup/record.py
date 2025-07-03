import os
import signal
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from datetime import datetime
import subprocess

# === Settings ===
SAMPLE_RATE = 44100
CHANNELS = 1

# === Create directory if it doesn't exist ===
output_dir = os.path.expanduser("~/Downloads/recordings")
os.makedirs(output_dir, exist_ok=True)
FILENAME = os.path.join(output_dir, datetime.now().strftime("rec_%Y-%m-%d_%H-%M-%S.wav"))

# === Enable 48V Phantom Power (Scarlett control must be installed) ===
status = subprocess.run("amixer -c 3 get 'Line In 1 Phantom Power'", shell=True, capture_output=True, text=True)
phantom_status = "Mono: Capture [on]" in status.stdout
print(f"phantom power was {phantom_status}")
if not phantom_status:
    status_new = subprocess.run("amixer -c 3 set 'Line In 1 Phantom Power' toggle", shell=True, capture_output=True, text=True)
    phantom_status_new = "Mono: Capture [on]" in status_new.stdout
    print(f"phantom power is now {phantom_status_new}")

# === Find Scarlett Solo device ===
def get_scarlett_device():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if "Scarlett" in dev['name'] and dev['max_input_channels'] > 0:
            print(f"Using devicename:         {dev['name']}")
            return i
    raise RuntimeError("Scarlett Solo input device not found")

device_index = get_scarlett_device()
print(f"Using input device index: {device_index}")

# === Recording setup ===
recording = []
is_recording = True

def stop_recording(signum=None, frame=None):
    global is_recording
    print("Stopping recording...")
    is_recording = False

# === Handle Ctrl+C or system shutdown ===
signal.signal(signal.SIGINT, stop_recording)
signal.signal(signal.SIGTERM, stop_recording)

def audio_callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    if is_recording:
        recording.append(indata.copy())

# === Start Recording ===
print("Recording started. Press Ctrl+C to stop.")
with sd.InputStream(samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    callback=audio_callback,
                    device=device_index):
    try:
        while is_recording:
            sd.sleep(500)
    except KeyboardInterrupt:
        pass

# === Save to WAV ===
print("Saving file...")
audio_data = np.concatenate(recording, axis=0)
wav.write(FILENAME, SAMPLE_RATE, audio_data)
print(f"Saved: {FILENAME}")
