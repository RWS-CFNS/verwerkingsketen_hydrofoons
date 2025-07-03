import glob
import re
import os
import scipy.io.wavfile as wav
import numpy as np
import matplotlib.pyplot as plt

def load_wav_files():
    files = glob.glob("C:\\Users\\sepva\\Documents\\GitHub\\recordingModule\\recordings\\bad\\*.wav")
    pattern = r"rec_(\d+)_\d+_synced_\d+\.wav"
    output = []
    for file in files:
        match = re.search(pattern, os.path.basename(file))
        if match:
            output.append((int(match.group(1)), file))
    return output # (id, file_path)

def get_signals(files):
    fs = 0
    output = []

    for id, filepath in files:
        fs, sig = wav.read(filepath)
        output.append((id, sig))

    return output, fs # (id, sig)

def window_signals(signals, fs, start, end):
    start = int(start * fs)
    end = int(end * fs)
    windowed = [(id, sig[start:end]) for id, sig in signals]
    return windowed, fs

def compute_gcc_phat(x0, x1):
    # Compute FFTs
    X0 = np.fft.fft(x0)
    X1 = np.fft.fft(x1)
    
    # Cross spectrum
    S = X0 * np.conj(X1)

    # PHAT weighting
    S /= np.abs(S) + 1e-10

    # Phase difference
    phase_diff = np.angle(S)

    # Time domain: Cross-correlation
    psi = np.real(np.fft.ifft(S))
    psi_shifted = np.fft.fftshift(psi)
    N = len(x0)
    lags = np.arange(-N//2, N//2)

    center = len(psi_shifted) // 2
    
    return psi_shifted, lags, phase_diff, center




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







# define expected stuff
# do window_signals for all signals
# create a list of signal pairs (id, id) for all signals
# do compute_gcc_phat for each signal pair
# calc estimations
# do plot for each signal pair (unwrapped phase diff and cross-correlation)
# create a txt file with the results

files = load_wav_files()
signals, fs = get_signals(files)
# signals, fs = window_signals(signals, fs, 8, 9)

expected_delay = int(0.5 * 0.297 / 343 * fs)
expected_max_delay = int(1.5 * 0.297 / 343 * fs)

signal_pairs = [((id1, sig1), (id2, sig2))
                for i, (id1, sig1) in enumerate(signals)
                for j, (id2, sig2) in enumerate(signals)
                if i < j]

# Create a single figure with a 3x2 grid of subplots
fig, axs = plt.subplots(3, 2, figsize=(15, 12))
axs = axs.flatten()

# open a file to save results
with open("C:\\Users\\sepva\\Documents\\GitHub\\recordingModule\\recordings\\results.txt", "a") as f:

    for idx, ((id1, sig1), (id2, sig2)) in enumerate(signal_pairs):
        # Compute GCC-PHAT
        psi_shifted, lags, phase_diff, center = compute_gcc_phat(sig1, sig2)

        # Estimate delay within the expected range
        valid_window = psi_shifted[center - expected_max_delay:center + expected_max_delay]
        # peak_idx = find_best_peak(valid_window)
        peak_idx = np.argmax(valid_window)
        estimated_delay = peak_idx - expected_max_delay
        # estimated_delay = np.argmax(psi_shifted[center-expected_max_delay:center+expected_max_delay]) - expected_max_delay
        estimated_distance = estimated_delay / fs * 343 / 2 * 100

        peak = np.max(valid_window)
        noise_floor = np.max(np.mean(valid_window), 0) + 1e-9 # avoid division by zero
        noise = np.mean(noise_floor)
        snr = np.abs(peak / noise)

        

        print(f"Signal pair ({id1}, {id2}): Estimated distance from center: {estimated_distance:.2f} cm")
        print(f"peak: {peak:.2f}, noise_floor: {noise_floor:.2f}, noise: {noise:.2f}, SNR: {snr:.2f}")

        idx = idx * 2

        # Plot phase difference across frequencies
        axs[idx].plot(np.unwrap(phase_diff), label="Unwrapped Phase Difference")
        axs[idx].set_title("Phase Difference (X0 * conj(X1))")
        axs[idx].set_xlabel("Frequency bin")
        axs[idx].set_ylabel("Phase (radians)")
        axs[idx].grid(True)
        axs[idx].legend()

        # Plot cross-correlation
        axs[idx+1].plot(lags, psi_shifted)
        axs[idx+1].axvline(expected_delay, color='red', linestyle=':', label=f"Expected Delay ({expected_delay})")
        axs[idx+1].axvline(expected_max_delay, color='red', linestyle='--', label=f"Expected Max Delay ({expected_max_delay})")
        axs[idx+1].axvline(estimated_delay, color='green', linestyle='--', label=f"Estimated Delay ({estimated_delay})")
        axs[idx+1].set_title(f"Cross-Correlation (GCC-PHAT) for Signal Pair ({id1}, {id2})")
        axs[idx+1].set_xlabel("Lags (samples)")
        axs[idx+1].set_ylabel("Amplitude")
        axs[idx+1].legend(loc='upper left')
        axs[idx+1].grid(True)
        axs[idx+1].text(0.95, 0.95, f"Estimated Distance From Center: {estimated_distance:.2f} cm", transform=axs[idx+1].transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', color='green')
        axs[idx+1].set_xlim(-2*expected_max_delay, 2*expected_max_delay)
        
        # Save results to a text file
        f.write(f"Signal pair ({id1}, {id2}): Estimated distance from center: {estimated_distance:.2f} cm\n")

plt.tight_layout()
plt.show()

f.close()
print("Results saved to results.txt")