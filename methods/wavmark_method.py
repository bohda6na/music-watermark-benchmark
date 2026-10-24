
import numpy as np
import torch
import wavmark

from scripts.common import SR, resample


class WavMarkWatermarker:
    name = "wavmark"

    def __init__(self, device=None, decode_batch_size=10):
        self.decode_batch_size = decode_batch_size
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

        # WavMark works at 16 kHz. Add only the watermark (watermarked - x16),
        # upsampled to sr, to the original, so the content above 8 kHz is kept.
        residual = resample(watermarked - x16, 16000, sr)
        residual = np.pad(
            residual, (0, max(0, len(x) - len(residual)))
        )[:len(x)]
        return (x + residual).astype(np.float32)

    def detect(self, y, sr=SR):
        y16 = resample(y, sr, 16000)

        # decode_batch_size only sets how many windows go to the model at once;
        # every window is decoded on its own, so the result does not depend on it.
        decoded, _ = wavmark.decode_watermark(
            self.model,
            y16,
            decode_batch_size=self.decode_batch_size,
            show_progress=False
        )

        if decoded is None:
            return None

        return np.asarray(decoded, dtype=np.int64)
