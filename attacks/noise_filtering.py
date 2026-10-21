
import numpy as np


def gaussian_noise(x, snr_db, seed=42):
    """Add Gaussian noise with a specified SNR."""
    x = np.asarray(x, dtype=np.float32)

    signal_power = np.mean(x ** 2)

    if signal_power == 0:
        return x.copy()

    noise_power = signal_power / (10 ** (snr_db / 10))

    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, size=x.shape)

    noise *= np.sqrt(
        noise_power / np.mean(noise ** 2)
    )

    return (x + noise).astype(np.float32)

from scipy.signal import butter, sosfiltfilt


def lowpass_filter(x, sr=44100, cutoff=3000, order=5):
    """Remove frequencies above cutoff."""
    sos = butter(
        order, cutoff, btype="lowpass",
        fs=sr, output="sos"
    )
    return sosfiltfilt(sos, x).astype(np.float32)


def highpass_filter(x, sr=44100, cutoff=300, order=5):
    """Remove frequencies below cutoff."""
    sos = butter(
        order, cutoff, btype="highpass",
        fs=sr, output="sos"
    )
    return sosfiltfilt(sos, x).astype(np.float32)

from scipy.signal import fftconvolve


def reverberation(x, sr=44100, decay=0.4, delay_ms=50, repeats=5):
    """Simulate reverberation using multiple decaying echoes."""
    x = np.asarray(x, dtype=np.float32)

    delay_samples = int(sr * delay_ms / 1000)
    if delay_samples < 1:
        raise ValueError("delay_ms is too small")

    impulse = np.zeros(delay_samples * repeats + 1)
    impulse[0] = 1.0

    for i in range(1, repeats + 1):
        impulse[i * delay_samples] = decay ** i

    y = fftconvolve(x, impulse, mode="full")[:len(x)]

    return y.astype(np.float32)
