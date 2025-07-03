import glob
import re
import os
import scipy.io.wavfile as wav
import numpy as np
import time

def load_wav_files():
    files = glob.glob("C:\\Users\\sepva\\Documents\\GitHub\\recordingModule\\recordings\\*.wav")
    pattern = r"rec_\d+_(\d+)\.wav"
    output = []
    for file in files:
        match = re.search(pattern, os.path.basename(file))
        if match:
            output.append((int(match.group(1)), file))
    return output  # (timestamp, file_path)

def get_signals(files):
    fs = 0
    sigs = []
    times = []

    for timestamp, filepath in files:
        fs, sig = wav.read(filepath)
        sig = sig[:, 0]  # use only first channel
        sigs.append(sig)
        times.append(timestamp)

    # Align based on timestamp offsets
    max_time = max(times)
    corrected = []
    for t, sig in zip(times, sigs):
        offset_samples = int((max_time - t) / 1e9 * fs)
        trimmed = sig[offset_samples:]
        corrected.append(trimmed)

    # Trim all to the shortest signal
    min_len = min(map(len, corrected))
    aligned = [sig[:min_len] for sig in corrected]

    return aligned, fs, [file[1] for file in files]  # signals, fs, filenames

counter = 0
def save_synced_wavs():
    global counter
    files = load_wav_files()
    if len(files) > 1:
        signals, fs, filenames = get_signals(files)
        for signal, original_path in zip(signals, filenames):
            wav.write(original_path[:-4] + "_synced_" + str(counter) + ".wav", fs, signal)
            os.remove(original_path)
        counter += 1

while True:
    save_synced_wavs()
    time.sleep(0.1)
