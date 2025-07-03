import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
from scipy.fft import fft, ifft

# Parameters
fs = 8000  # sampling frequency in Hz
delay_seconds_a = 0.002  # actual delay in seconds (2ms)
delay_samples_a = int(fs * delay_seconds_a)

# Simulated signal: a simple short burst
N = 1024
x1 = np.zeros(N)
x1[100:110] = np.hanning(10)  # a short pulse

# Delayed version of the signal
x0 = np.zeros(N)
x0[100 + delay_samples_a:110 + delay_samples_a] = np.hanning(10)

# print the two signals
print("delay_samples:", delay_samples_a)
print("Signal x0:", x0[90:110+delay_samples_a])
print("Signal x1:", x1[90:110+delay_samples_a])

def gcc_phat(x0, x1, K):
    """Compute GCC-PHAT with window length K."""
    X0 = fft(x0[:K]) # With (negative) delay
    X1 = fft(x1[:K]) # Reference signal
    S = X0 * np.conj(X1)
    S /= np.abs(S) + 1e-10  # PHAT weighting
    psi = np.real(ifft(S))
    psi = np.fft.fftshift(psi)
    m = np.arange(-K // 2, K // 2)
    return m, psi

def estimate_delay(psi, fs):
    """Estimate delay from GCC-PHAT result."""
    m = np.argmax(psi)
    center = len(psi) // 2
    delay_samples = m - center
    print("m:", m)
    print("center:", center)
    print("delay_samples:", delay_samples + center)
    print("delay_samples:", delay_samples)
    # if delay_samples > 0:
    #     delay_samples = len(psi)
    return delay_samples / fs

# Try with different K values
K_values = [128, 64, 256]
fig, axs = plt.subplots(len(K_values), 1, figsize=(8, 10), sharex=True)

for i, K in enumerate(K_values):
    m, psi = gcc_phat(x0, x1, K)
    delay_estimated = estimate_delay(psi, fs)
    axs[i].plot(m, psi)
    axs[i].set_title(f'GCC-PHAT with K = {K}, Estimated Delay = {delay_estimated:.6f} s')
    axs[i].axvline(delay_samples_a, color='red', linestyle='--', label='True Delay')
    axs[i].legend()
    axs[i].grid(True)

plt.xlabel('Delay (samples)')
plt.tight_layout()
plt.show()
