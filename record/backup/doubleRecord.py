import os
import threading
import signal
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from datetime import datetime
import time
import subprocess

SAMPLE_RATE = 44100
CHANNELS = 1
OUTPUT_DIR = os.path.expanduser("~/Downloads/recordings")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Get audio controls ===
def get_audio_controls():
    controls = subprocess.run("awk 'NR % 2 == 1' /proc/asound/cards", shell=True, capture_output=True, text=True).stdout.splitlines()
    print(f"Audio controls:")
    for line in controls:
        print(line)
    print("")
    return [int(line.split()[0]) for line in controls if "Scarlett" in line]

# === Enable 48V Phantom Power ===
def enable_phantom_power(audio_controls):
    print(f"Audio control indexs: {audio_controls}")
    for i in audio_controls:
        phantom_on = "Mono: Capture [on]" in subprocess.run(f"amixer -c {i} get 'Line In 1 Phantom Power'", shell=True, capture_output=True, text=True).stdout
        print(f"Phantom power status for device {i} is {'on' if phantom_on else 'off'}")
        if not phantom_on:
            phantom_on = "Mono: Capture [on]" in subprocess.run(f"amixer -c {i} set 'Line In 1 Phantom Power' toggle", shell=True, capture_output=True, text=True).stdout
        print(f"Phantom power status for device {i} is now {'on' if phantom_on else 'off'}")

# === Get audio devices ===
def get_audio_devices():
    devices = sd.query_devices()
    audio_devices = []
    for i, device in enumerate(devices):
        if "Scarlett" in device['name'] and device['max_input_channels'] > 0:
            print(f"Found: {device['name']}")
            audio_devices.append(i)
    return audio_devices

# === Overwrite interrupt and shutdown procedures ===
is_recording = True
def stop_recording(signum=None, frame=None):
    global is_recording
    print("Stopping all recordings...")
    is_recording = False
signal.signal(signal.SIGINT, stop_recording)
signal.signal(signal.SIGTERM, stop_recording)



def record_from_device(device_index):
    print(f"Starting recording on device {device_index}")
    recording = []

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[Device {device_index}]:", status)
        if is_recording:
            recording.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE,
                        channels=CHANNELS,
                        callback=audio_callback,
                        device=device_index):
        start_time = time.time()
        while is_recording:
            sd.sleep(500)
    
    filename = os.path.join(OUTPUT_DIR, datetime.fromtimestamp(start_time).strftime(f"rec{device_index}_%Y-%m-%d_%H-%M-%S.%f.wav"))
    audio_data = np.concatenate(recording, axis=0)
    wav.write(filename, SAMPLE_RATE, audio_data)
    print(f"Saved from device {device_index} to {filename}")

# === Main logic ===
audio_controls = get_audio_controls()
enable_phantom_power(audio_controls)
audio_devices = get_audio_devices()
if len(audio_devices) < 2:
    print("Error: Less than 2 input devices available.")
else:
    threads = []
    for i in range(len(audio_devices)):
        t = threading.Thread(target=record_from_device, args=(audio_devices[i],))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    print("All recordings finished.")