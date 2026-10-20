"""audiowmark wrapper (https://github.com/swesterfeld/audiowmark), classical spread spectrum.

audiowmark is a command-line tool, so every call goes through a temporary 16-bit WAV file.
We use its short-message mode (`--short 16`) to embed the shared 16-bit message.

    embed:  x -> temp WAV -> `audiowmark add` -> watermarked signal (same sample rate)
    detect: y -> temp WAV -> `audiowmark get`  -> decoded 16 bits, or None if no pattern found
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from scripts.common import SR, to_mono


class AudiowmarkWatermarker:
    name = "audiowmark"

    def __init__(self) -> None:
        if shutil.which("audiowmark") is None:
            raise RuntimeError(
                "audiowmark not found in PATH. Build it from "
                "https://github.com/swesterfeld/audiowmark (Linux / Colab)."
            )

    @staticmethod
    def _to_hex(message: np.ndarray) -> str:
        bits = "".join(str(int(b)) for b in message)
        return f"{int(bits, 2):0{len(bits) // 4}x}"

    def embed(self, x: np.ndarray, message: np.ndarray, sr: int = SR) -> np.ndarray:
        """Return the watermarked signal at the input sample rate."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "in.wav", Path(tmp) / "out.wav"
            sf.write(src, np.clip(x, -1.0, 1.0), sr, subtype="PCM_16")
            subprocess.run(
                ["audiowmark", "add", "--short", str(len(message)), str(src), str(dst),
                 self._to_hex(message)],
                check=True,
                capture_output=True,
            )
            xw, _ = sf.read(dst, dtype="float32")
        return to_mono(xw).astype(np.float32)

    def detect(self, y: np.ndarray, sr: int = SR, nbits: int = 16, extra: tuple = ()):
        """Return the decoded bits (np.ndarray) or None if no watermark was found.

        `extra` are additional audiowmark flags, e.g. ("--detect-speed",).
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.wav"
            sf.write(path, np.clip(y, -1.0, 1.0), sr, subtype="PCM_16")
            out = subprocess.run(
                ["audiowmark", "get", "--short", str(nbits), *extra, str(path)],
                capture_output=True,
                text=True,
            ).stdout
        m = re.search(r"^pattern\s+\S+\s+([0-9a-f]+)", out, re.M)
        if not m:
            return None
        bits = bin(int(m.group(1), 16))[2:].zfill(nbits)
        return np.array([int(c) for c in bits], dtype=np.int64)