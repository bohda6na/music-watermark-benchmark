"""Compression attacks: MP3, AAC (ffmpeg) and, optionally, the EnCodec neural codec.

Every attack takes a mono float32 signal at 44.1 kHz and returns a signal of the same
length and sample rate, so it can be applied to any watermarking method.

    from attacks.compression import mp3, aac, encodec, COMPRESSION_ATTACKS
    y = mp3(x, bitrate_kbps=64)
"""

from __future__ import annotations

import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

from scripts.common import SR, ffmpeg_decode, ffmpeg_exe, fit_length, resample, write_wav

BITRATES_KBPS = (128, 64, 32)
ENCODEC_BANDWIDTHS_KBPS = (24.0, 12.0, 6.0, 3.0, 1.5)


def _ffmpeg_roundtrip(x: np.ndarray, sr: int, codec_args: list[str], ext: str) -> np.ndarray:
    """Encode x with ffmpeg, decode it back, and align the length to the input."""
    with tempfile.TemporaryDirectory() as tmp:
        src, enc = Path(tmp) / "in.wav", Path(tmp) / f"out{ext}"
        write_wav(src, x, sr)
        cmd = [ffmpeg_exe(), "-v", "error", "-y", "-i", str(src), "-ac", "1", *codec_args, str(enc)]
        subprocess.run(cmd, capture_output=True, check=True)
        y = ffmpeg_decode(enc, sr)
    return fit_length(y, len(x))


def mp3(x: np.ndarray, bitrate_kbps: int = 128, sr: int = SR) -> np.ndarray:
    """MP3 (LAME, constant bitrate)."""
    return _ffmpeg_roundtrip(x, sr, ["-c:a", "libmp3lame", "-b:a", f"{bitrate_kbps}k"], ".mp3")


def aac(x: np.ndarray, bitrate_kbps: int = 128, sr: int = SR) -> np.ndarray:
    """AAC-LC (ffmpeg native encoder) in an .m4a container."""
    return _ffmpeg_roundtrip(x, sr, ["-c:a", "aac", "-b:a", f"{bitrate_kbps}k"], ".m4a")


@lru_cache(maxsize=1)
def _encodec_model(device: str):
    from encodec import EncodecModel

    return EncodecModel.encodec_model_24khz().to(device).eval()


def encodec(x: np.ndarray, bandwidth_kbps: float = 6.0, sr: int = SR) -> np.ndarray:
    """EnCodec 24 kHz (Meta) neural codec. Optional: needs `pip install encodec`."""
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = _encodec_model(device)
    model.set_target_bandwidth(bandwidth_kbps)
    x24 = resample(x, sr, model.sample_rate)
    with torch.no_grad():
        wav = torch.from_numpy(x24)[None, None].to(device)
        y24 = model.decode(model.encode(wav)).squeeze().cpu().numpy()
    return fit_length(resample(y24, model.sample_rate, sr), len(x))


def compression_attacks(include_neural: bool = False) -> list[tuple[str, str, callable]]:
    """List of (attack, params, fn) with fn(x) -> attacked x."""
    out = []
    for name, fn in (("mp3", mp3), ("aac", aac)):
        for b in BITRATES_KBPS:
            out.append((name, f"{b}kbps", lambda x, fn=fn, b=b: fn(x, b)))
    if include_neural:
        for bw in ENCODEC_BANDWIDTHS_KBPS:
            out.append(("encodec", f"{bw:g}kbps", lambda x, bw=bw: encodec(x, bw)))
    return out
