"""Shared helpers for the benchmark scripts: audio loading, ffmpeg, metrics, CSV.

Conventions (see data/README.md):
- audio is mono, 44.1 kHz, float32 in [-1, 1];
- every method embeds the same 16-bit message;
- a watermark counts as detected when bit accuracy >= 14/16.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 44100
MESSAGE = "1011001110001101"  # shared 16-bit message, same for all methods
DETECT_MIN_BITS = 14  # detected if at least 14 of 16 bits are correct

CSV_COLUMNS = [
    "method", "attack", "params", "genre", "track_id",
    "detected", "snr", "bit_acc", "detect_prob",
]

REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTION_CSV = REPO_ROOT / "data" / "selected_80.csv"


# ---------- ffmpeg ----------

@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    """ffmpeg from PATH, or the static build shipped with the imageio-ffmpeg package."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as e:
        raise RuntimeError(
            "ffmpeg not found. Install it (apt install ffmpeg) or `pip install imageio-ffmpeg`."
        ) from e


def ffmpeg_decode(path: str | Path, sr: int = SR) -> np.ndarray:
    """Decode any audio file to a mono float32 array at `sr`."""
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(path),
           "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


# ---------- audio ----------

def to_mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x.astype(np.float32)
    g = np.gcd(sr_in, sr_out)
    return resample_poly(x, sr_out // g, sr_in // g).astype(np.float32)


def fit_length(x: np.ndarray, n: int) -> np.ndarray:
    """Trim or zero-pad to exactly n samples (codecs add/remove a few samples)."""
    if len(x) >= n:
        return x[:n]
    return np.pad(x, (0, n - len(x)))


def load_audio(path: str | Path, sr: int = SR) -> np.ndarray:
    path = Path(path)
    if path.suffix.lower() in {".wav", ".flac"}:
        x, file_sr = sf.read(path, dtype="float32", always_2d=False)
        return resample(to_mono(x), file_sr, sr)
    return ffmpeg_decode(path, sr)


def find_track(track_id: int, wav_dir: Path | None, fma_dir: Path | None) -> Path:
    """Find a track as WAV (000002.wav or 2.wav) or as the original FMA mp3 (000/000002.mp3)."""
    tid = f"{track_id:06d}"
    candidates = []
    if wav_dir is not None:
        candidates += [wav_dir / f"{tid}.wav", wav_dir / f"{track_id}.wav"]
    if fma_dir is not None:
        candidates += [fma_dir / tid[:3] / f"{tid}.mp3", fma_dir / f"{tid}.mp3"]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Track {track_id} not found. Tried: {[str(c) for c in candidates]}")


def write_wav(path: str | Path, x: np.ndarray, sr: int = SR) -> None:
    sf.write(path, np.clip(x, -1.0, 1.0), sr, subtype="FLOAT")


# ---------- metrics ----------

def snr_db(original: np.ndarray, processed: np.ndarray) -> float:
    """SNR = 10*log10( sum(x^2) / sum((x - x_w)^2) )."""
    n = min(len(original), len(processed))
    x, y = original[:n].astype(np.float64), processed[:n].astype(np.float64)
    noise = np.sum((x - y) ** 2)
    if noise == 0:
        return float("inf")
    return float(10 * np.log10(np.sum(x**2) / noise))


def bits_from_str(s: str) -> np.ndarray:
    assert set(s) <= {"0", "1"}, "message must be a string of 0/1"
    return np.array([int(c) for c in s], dtype=np.int64)


def bit_accuracy(decoded: np.ndarray, message: np.ndarray) -> float:
    return float(np.mean(np.asarray(decoded) == np.asarray(message)))


def is_detected(bit_acc: float, nbits: int = 16) -> bool:
    return round(bit_acc * nbits) >= DETECT_MIN_BITS


# ---------- selection / CSV ----------

def read_selection(path: Path = SELECTION_CSV) -> list[tuple[int, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [(int(r["track_id"]), r["genre"]) for r in csv.DictReader(f)]


def done_keys(csv_path: Path) -> set[tuple[str, str, str]]:
    """(track_id, attack, params) rows already in the CSV, so a run can be resumed."""
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {(r["track_id"], r["attack"], r["params"]) for r in csv.DictReader(f)}


def append_rows(csv_path: Path, rows: list[dict]) -> None:
    new = not csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if new:
            w.writeheader()
        w.writerows(rows)
