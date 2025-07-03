import glob
import re
import os
import scipy.io.wavfile as wav
import numpy as np
import matplotlib.pyplot as plt

def load_wav_files():
    files = glob.glob("C:\\Users\\sepva\\Documents\\GitHub\\recordingModule\\recordings\\*.wav")
    pattern = r"rec_\d+_(\d+)\.wav"
    output = []
    for file in files:
        match = re.search(pattern, os.path.basename(file))
        if match:
            output.append((int(match.group(1)), file))
    return output # (timestamp, file_path)

def get_signals():
    files = load_wav_files()
    files.sort(key=lambda x: x[0])
    
    fs, sig0 = wav.read(files[0][1])
    _, sig1 = wav.read(files[1][1])

    sig0 = sig0[:, 0]
    sig1 = sig1[:, 0]

    t0, t1 = files[0][0], files[1][0]
    offset_samples_correction = int(abs(t0 - t1) / 1000000000 * fs)

    # offset_samples_correction = 300 # example TODO ---------------------------------------------------

    # print(f"Offset correction in samples was: {offset_samples_correction}")

    x0 = sig0[offset_samples_correction:]
    x1 = sig1[:len(sig1)-offset_samples_correction]

    return x0, x1, fs

def window_signals(x0, x1, fs, start, end):
    start = int(start * fs)
    end = int(end * fs)
    x0 = x0[start:end]
    x1 = x1[start:end]
    return x0, x1, fs

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



x0, x1, fs = get_signals()
# x0, x1, fs = window_signals(x0, x1, fs, 3.86, 3.96)
# x0, x1, fs = window_signals(x0, x1, fs, 3, 5)

psi_shifted, lags, phase_diff, center = compute_gcc_phat(x0, x1)
expected_delay = int(1 * 0.297 / 343 * fs)
expected_max_delay = int(3 * 0.297 / 343 * fs)
# estimated_delay = np.argmax(psi_shifted) - center
estimated_delay = np.argmax(psi_shifted[center-expected_max_delay:center+expected_max_delay]) - expected_max_delay
estimated_distance = estimated_delay / fs * 343 / 2 * 100
print(f"Estimated distance from center: {estimated_distance:.2f} cm")

fig, axs = plt.subplots(3, 1, figsize=(10, 8))

# Plot original and delayed signal
n = np.arange(len(x0))
axs[0].stem(n, x0, linefmt='C1-', markerfmt='x', basefmt=" ", label="x0 (delayed)")
axs[0].stem(n, x1, linefmt='gray', markerfmt='o', basefmt=" ", label="x1 (reference)")

axs[0].legend()
axs[0].set_title("Signals in Time Domain")
axs[0].set_xlabel("Samples")
# axs[0].set_xlim(6000, 10000)
# Add secondary x-axis for time (seconds)
def samples_to_time(x): return x / fs
def time_to_samples(x): return x * fs
secax = axs[0].secondary_xaxis('top', functions=(samples_to_time, time_to_samples))
secax.set_xlabel("Time (s)")

# Plot phase difference across frequencies
axs[1].plot(np.unwrap(phase_diff), label="Unwrapped Phase Difference")
axs[1].set_title("Phase Difference (X0 * conj(X1))")
axs[1].set_xlabel("Frequency bin")
axs[1].set_ylabel("Phase (radians)")
axs[1].grid(True)
axs[1].legend()

# Plot cross-correlation
axs[2].plot(lags, psi_shifted)
axs[2].axvline(expected_delay, color='red', linestyle=':', label=f"Expected Delay ({expected_delay})")
axs[2].axvline(expected_max_delay, color='red', linestyle='--', label=f"Expected Max Delay ({expected_max_delay})")
axs[2].axvline(estimated_delay, color='green', linestyle='--', label=f"Estimated Delay ({estimated_delay})")
axs[2].set_title("Cross-Correlation (GCC-PHAT)")
axs[2].set_xlabel("Lags (samples)")
axs[2].set_ylabel("Amplitude")
axs[2].legend(loc='upper left')
axs[2].grid(True)
axs[2].text(0.95, 0.95, f"Estimated Distance From Center: {estimated_distance:.2f} cm", transform=axs[2].transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', color='green')
# axs[2].set_xlim(-200, 200)
axs[2].set_xlim(-2*expected_max_delay, 2*expected_max_delay)

plt.tight_layout()
plt.show()
