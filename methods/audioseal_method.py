"""AudioSeal wrapper (https://github.com/facebookresearch/audioseal).

The AudioSeal models work at 16 kHz. Since version 0.2 the library does NOT resample
internally (the `sample_rate` argument is ignored with a warning), so we do it here:

    embed:  x (44.1k) -> 16k -> generator -> watermark (16k) -> 44.1k -> x + watermark
    detect: y (44.1k) -> 16k -> detector -> (detection probability, 16 bits)

Adding the upsampled watermark to the original 44.1 kHz signal keeps everything above
8 kHz untouched, so the track itself is not downsampled.
"""

from __future__ import annotations

import os

# AudioSeal 0.2 wraps its layers in torch.compile, which needs a C++ compiler
# (fails on Windows without MSVC) and gives no real speed-up for a few dozen tracks.
os.environ.setdefault("NO_TORCH_COMPILE", "1")

import numpy as np  # noqa: E402
import torch

from scripts.common import SR, resample

MODEL_SR = 16000


class AudioSealWatermarker:
    name = "audioseal"

    def __init__(self, device: str | None = None):
        from audioseal import AudioSeal

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.generator = AudioSeal.load_generator("audioseal_wm_16bits").to(self.device).eval()
        self.detector = AudioSeal.load_detector("audioseal_detector_16bits").to(self.device).eval()

    def _tensor(self, x: np.ndarray) -> torch.Tensor:
        return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32))[None, None].to(self.device)

    @torch.no_grad()
    def embed(self, x: np.ndarray, message: np.ndarray, sr: int = SR) -> np.ndarray:
        """Return the watermarked signal at the input sample rate (same length)."""
        x16 = resample(x, sr, MODEL_SR)
        msg = torch.as_tensor(message, dtype=torch.int64)[None].to(self.device)
        wm16 = self.generator.get_watermark(self._tensor(x16), message=msg)
        wm = resample(wm16.squeeze().cpu().numpy(), MODEL_SR, sr)
        wm = np.pad(wm, (0, max(0, len(x) - len(wm))))[: len(x)]
        return (x + wm).astype(np.float32)

    @torch.no_grad()
    def detect(self, y: np.ndarray, sr: int = SR) -> tuple[float, np.ndarray]:
        """Return (probability that the audio is watermarked, decoded 16 bits)."""
        y16 = resample(y, sr, MODEL_SR)
        prob, bits = self.detector.detect_watermark(self._tensor(y16), message_threshold=0.5)
        return float(prob.item()), bits.squeeze(0).cpu().numpy().astype(np.int64)
