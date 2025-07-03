import glob
import re
import os
import time
import scipy.io.wavfile as wav
import numpy as np
import argparse

# Store files that belong together
def load_grouped_wav_files(folder):
    pattern = r"rec_(\d+)_(\d+)_synced_(\d+)\.wav"
    files = glob.glob(os.path.join(folder, "*.wav"))
    grouped = {}  
    for file in files:
        name = os.path.basename(file)
        match = re.match(pattern, name)
        if match:
            mic_id, _, sync_id = map(int, match.groups())
            grouped.setdefault(sync_id, []).append((mic_id, file))
    return grouped # {sync_id: [(mic_id, file_path), ...]}

# Extract signals as numpy arrays and determine sampling rate
def get_signals(files):
    fs = 0
    output = []
    for id, filepath in files:
        fs, sig = wav.read(filepath)
        output.append((id, sig))
    return output, fs # (id, sig)

# Compute the GCC-PHAT, check https://github.com/nathalisr/GCC-PHAT for explanation
def compute_gcc_phat(x0, x1):
    X0 = np.fft.fft(x0) # FFT of first signal
    X1 = np.fft.fft(x1) # FFT of second signal
    S = X0 * np.conj(X1) # Cross spectrum
    S /= np.abs(S) + 1e-10 # PHAT weighting
    psi = np.real(np.fft.ifft(S)) # Inverse FFT to get cross-correlation
    psi_shifted = np.fft.fftshift(psi) # Shift zero-lag to center
    N = len(x0)
    lags = np.arange(-N // 2, N // 2) # Create matching lag array for x-axis
    center = len(psi_shifted) // 2
    return psi_shifted, lags, center

# Find the point of maximum correlation whilst avoiding misleading noise peaks
def find_best_peak(valid_window, max_tries=5):
    window = valid_window.copy()
    tried = 0

    while tried < max_tries:
        idx = np.argmax(window)
        if idx < 2 or idx > len(window) - 3:
            window[idx] = -0.001  # skip if near the edge
            tried += 1
            continue

        if ((window[idx - 2] > 0 and window[idx - 1] > 0) or
            (window[idx + 1] > 0 and window[idx + 2] > 0)):
            return idx  # found acceptable peak

        window[idx] = -0.001  # invalidate this peak
        tried += 1

    return len(window) // 2  # fallback to center (0 delay)

def process_signal_pairs(sync_id, signal_pairs, fs, f):
    # Set the expected maximum delay based on the distance between hydrophones (now set to 10 A4-lengths)
    expected_max_delay = int(2 * 0.297 / 343 * fs)

    for (id1, sig1), (id2, sig2) in signal_pairs:
        try:
            psi_shifted, lags, center = compute_gcc_phat(sig1, sig2)
            
            # Only search for time delays in the expected range
            valid_window = psi_shifted[center - expected_max_delay:center + expected_max_delay]
            peak_idx = find_best_peak(valid_window)
            estimated_delay = peak_idx - expected_max_delay
            estimated_distance = estimated_delay / fs * 343 / 2 * 100  # 343 m/s, 2 relative to center, 100 cm

            # Calculate SNR
            peak = np.max(valid_window)
            noise_floor = np.mean(valid_window) + 1e-9 # avoid division by zero
            noise = np.mean(noise_floor)
            snr = np.abs(peak / noise)
            # snr = 20 * np.log10(snr)

            # Save results
            result = f"[Group {sync_id}] Signal pair ({id1}, {id2}): Estimated distance from center: {estimated_distance:.2f} cm. SNR: {snr:.2f}"
            
            f.write(result + "\n")

        except ValueError as e:
            print(f"[Group {sync_id}]:", e)

def calculate_signal_pairs(grouped_files, f, mode):
    for sync_id, files in grouped_files.items():
        # Check if there are at least 3 signals
        if ((mode == "test" and len(files) < 2) or (mode == "demo" and len(files) < 3)):
            continue

        signals, fs = get_signals(files)

        # Create all possible pairs of signals
        signal_pairs = [((id1, sig1), (id2, sig2))
                        for i, (id1, sig1) in enumerate(signals)
                        for j, (id2, sig2) in enumerate(signals)
                        if i < j]
        
        process_signal_pairs(sync_id, signal_pairs, fs, f)
            
        # Delete files in this group
        for _, path in files:
            os.remove(path)

def main():
    # Get mode from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["test", "demo", "field"], help="python ./analyze.py <test|demo|field> (<mode>)")
    args = parser.parse_args()

    # Input and output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../recordings"))
    output_file = os.path.join(folder, "results.txt")

    while True:
        grouped_files = load_grouped_wav_files(folder)

        # Sleep to avoid busy waiting
        if not grouped_files:
            time.sleep(0.1)
            continue

        with open(output_file, "a") as f:
            calculate_signal_pairs(grouped_files, f, args.mode)

if __name__ == "__main__":
    main()