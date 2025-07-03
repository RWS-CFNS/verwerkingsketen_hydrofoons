import glob
import re
import os
import scipy.io.wavfile as wav
import numpy as np
import time
import argparse

# Input
def load_wav_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../recordings"))

    files = glob.glob(folder + "\\*.wav")
    pattern = r"rec_\d+_(\d+)\.wav"
    output = []
    for file in files:
        match = re.search(pattern, os.path.basename(file))
        if match:
            output.append((int(match.group(1)), file))
    return output  # [(timestamp, file_path)]

# Extract signals, find timestamp and pulse, synchronize on pulse (and timestamp), remove pulse, trim signals
def get_signals(files, mode):
    fs = 0
    sigs = []
    clock_times = [] # in nanoseconds
    pulse_times = [] # in samples

    # Retrieve clock times from filenames
    for timestamp, filepath in files:
        fs, sig = wav.read(filepath)
        sig = sig[:, 0]  # use only first channel
        sigs.append(sig)
        clock_times.append(timestamp)

    # Find pulse times in signals
    ceiling = 2**31 - 1000
    floor = -2**31 + 1000

    if not mode == "test":
        for sig in sigs:
            i = 0
            if mode == "demo":
                i = int(0.25 * len(sig))
            while i < len(sig) - 51:
                # Check if the current segment matches the window pattern
                if np.all(sig[i:i+50] < floor) and np.all(sig[i + 51] > floor):
                    pulse_times.append(i)
                    break
                # inverted pulse
                elif np.all(sig[i:i+50] > ceiling) and np.all(sig[i + 51] < ceiling):
                    pulse_times.append(i)
                    break
                else:
                    i += 1
    else:
        pulse_times = [0] * len(sigs)

    # Calculate estimated real recording start times (in ns)
    start_times = [c - (p / fs) * 1e9 for c, p in zip(clock_times, pulse_times)]

    if mode == "test":
        start_times = clock_times
    
    # Use last start time as reference
    max_start_time = max(start_times)

    # Align signals based on their true start time offset
    corrected = []
    for start_time, sig, p in zip(start_times, sigs, pulse_times):

        # Calculate the offset in samples
        offset_samples = int((max_start_time - start_time) / 1e9 * fs)

        if mode == "demo":
            min_pulse_time = min(pulse_times)
            offset_samples = p - min_pulse_time # Overwrite because synchronization is only done based on the pulse
            sig = np.concatenate((sig[:p - 300], sig[p + 1500:])) # Remove pulse

        # Correct the signal by removing the offset
        corrected.append(sig[offset_samples:])

    # Trim all to same length
    min_len = min(map(len, corrected))
    aligned = [sig[:min_len] for sig in corrected]

    return aligned, fs, [file[1] for file in files]  # signals, fs, filenames

# Look for files, if found, sychronize them and change their name
def save_synced_wavs(counter, mode):
    files = load_wav_files()

    # Check if there are at least 3 signals
    if ((mode == "test" and len(files) > 1) or (mode == "demo" and len(files) > 2)):
        signals, fs, filenames = get_signals(files, mode)
        for signal, original_path in zip(signals, filenames):
            wav.write(original_path[:-4] + "_synced_" + str(counter) + ".wav", fs, signal)
            os.remove(original_path)

        # Remove remaining files to remove outdated buffered files
        files = load_wav_files()
        for _ , file_path in files:
            os.remove(file_path)
        counter += 1
    return counter


def main():
    # Get mode from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["test", "demo", "field"], help="python ./synchronize.py <test|demo|field> (<mode>)")
    args = parser.parse_args()

    print("Watching for synced recordings...")

    counter = 0
    while True:
        counter = save_synced_wavs(counter, args.mode)
        time.sleep(0.1)

if __name__ == "__main__":
    main()