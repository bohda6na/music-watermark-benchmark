"""Time and dynamics attacks: speed change, time stretch, pitch shift, gain, crop.

Every attack takes a mono float32 signal at 44.1 kHz and returns a mono float32 signal.
Unlike the compression attacks, speed, time stretch and crop CHANGE the length of the
signal (that is the point of the attack), so detectors must accept any length.

    from attacks.time_dynamics import time_dynamics_attacks
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
from scipy.signal import resample_poly

from scripts.common import SR

SPEED_FACTORS = (0.9, 0.95, 1.05, 1.1)
STRETCH_RATES = (0.9, 0.95, 1.05, 1.1)
PITCH_SEMITONES = (-2, -1, 1, 2)
GAIN_DB = (-6, 6)
CROP_KEEP = (0.5,)


def speed(x: np.ndarray, factor: float) -> np.ndarray:
    """Playback speed change: tempo and pitch change together (resampling).
    factor < 1 is slower (longer signal), factor > 1 is faster (shorter)."""
    f = Fraction(factor).limit_denominator(100)
    return resample_poly(x, f.denominator, f.numerator).astype(np.float32)


def time_stretch(x: np.ndarray, rate: float) -> np.ndarray:
    """Tempo change without changing pitch (librosa phase vocoder)."""
    import librosa

    return librosa.effects.time_stretch(x, rate=rate).astype(np.float32)


def pitch_shift(x: np.ndarray, semitones: float, sr: int = SR) -> np.ndarray:
    """Pitch change without changing tempo."""
    import librosa

    return librosa.effects.pitch_shift(x, sr=sr, n_steps=semitones).astype(np.float32)


def gain(x: np.ndarray, db: float) -> np.ndarray:
    """Volume change in dB, peaks are clipped to [-1, 1]."""
    return np.clip(x * 10 ** (db / 20), -1.0, 1.0).astype(np.float32)


def crop(x: np.ndarray, keep: float) -> np.ndarray:
    """Keep the first `keep` fraction of the track."""
    return x[: int(len(x) * keep)]


def time_dynamics_attacks() -> list[tuple[str, str, callable]]:
    """List of (attack, params, fn) with fn(x) -> attacked x."""
    out = []
    for p in SPEED_FACTORS:
        out.append(("speed", f"{p:g}x", lambda x, p=p: speed(x, p)))
    for r in STRETCH_RATES:
        out.append(("time_stretch", f"{r:g}x", lambda x, r=r: time_stretch(x, r)))
    for n in PITCH_SEMITONES:
        out.append(("pitch", f"{n:+d}st", lambda x, n=n: pitch_shift(x, n)))
    for d in GAIN_DB:
        out.append(("gain", f"{d:+d}dB", lambda x, d=d: gain(x, d)))
    for k in CROP_KEEP:
        out.append(("crop", f"keep{int(k * 100)}%", lambda x, k=k: crop(x, k)))
    return out