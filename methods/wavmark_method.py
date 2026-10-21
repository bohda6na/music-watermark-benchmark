
import numpy as np
import torch
import wavmark

from scripts.common import SR, resample


class WavMarkWatermarker:
    name = "wavmark"

    def __init__(self, device=None):
        self.device = device or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model = wavmark.load_model().to(self.device).eval()

    def embed(self, x, message, sr=SR):
        if len(message) != 16:
            raise ValueError("Expected 16-bit message")

        x16 = resample(x, sr, 16000)

        watermarked, _ = wavmark.encode_watermark(
            self.model,
            x16,
            np.asarray(message, dtype=np.int64),
            show_progress=False
        )

        y = resample(watermarked, 16000, sr)
        return np.pad(
            y, (0, max(0, len(x) - len(y)))
        )[:len(x)].astype(np.float32)

    def detect(self, y, sr=SR):
        y16 = resample(y, sr, 16000)

        decoded, _ = wavmark.decode_watermark(
            self.model,
            y16,
            show_progress=False
        )

        if decoded is None:
            return None

        return np.asarray(decoded, dtype=np.int64)
