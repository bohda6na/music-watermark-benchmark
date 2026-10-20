"""Sanity check for AudioSeal on 5 tracks: embed, then detect, with no attack.

Expected behaviour (AudioSeal README / paper): on watermarked audio the detection
probability is close to 1 and the 16-bit message is recovered exactly; on the
original (unwatermarked) audio the probability is close to 0 and the bits are random.

    python -m scripts.audioseal_smoke_test --wav-dir data/wav
    python -m scripts.audioseal_smoke_test --fma-dir data/raw/fma_small --save-dir data/interim/audioseal_smoke
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from methods.audioseal_method import AudioSealWatermarker
from scripts.common import (
    MESSAGE, bit_accuracy, bits_from_str, find_track, is_detected, load_audio,
    read_selection, snr_db, write_wav,
)


def pick_tracks(n: int) -> list[tuple[int, str]]:
    """First track of each genre, so the 5 tracks cover 5 different genres."""
    picked, seen = [], set()
    for tid, genre in read_selection():
        if genre not in seen:
            picked.append((tid, genre))
            seen.add(genre)
    return picked[:n]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wav-dir", type=Path, help="folder with mono 44.1 kHz WAVs (000002.wav)")
    p.add_argument("--fma-dir", type=Path, help="fma_small folder with the original mp3 files")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--save-dir", type=Path, help="optionally save original/watermarked WAVs to listen")
    p.add_argument("--device", default=None)
    args = p.parse_args()
    if not args.wav_dir and not args.fma_dir:
        p.error("give --wav-dir or --fma-dir")

    message = bits_from_str(MESSAGE)
    model = AudioSealWatermarker(args.device)
    print(f"device={model.device}  message={MESSAGE}\n")
    print(f"{'track':>7} {'genre':<14} {'SNR dB':>7} | {'p(wm)':>6} {'bits':>6} | {'p(orig)':>7} {'bits':>6} | {'sec':>5}")

    ok = True
    if args.save_dir:
        args.save_dir.mkdir(parents=True, exist_ok=True)
    for tid, genre in pick_tracks(args.n):
        t0 = time.time()
        x = load_audio(find_track(tid, args.wav_dir, args.fma_dir))
        xw = model.embed(x, message)
        p_wm, bits_wm = model.detect(xw)
        p_orig, bits_orig = model.detect(x)
        acc_wm, acc_orig = bit_accuracy(bits_wm, message), bit_accuracy(bits_orig, message)
        snr = snr_db(x, xw)

        print(f"{tid:>7} {genre:<14} {snr:>7.2f} | {p_wm:>6.3f} {round(acc_wm * 16):>3}/16 | "
              f"{p_orig:>7.3f} {round(acc_orig * 16):>3}/16 | {time.time() - t0:>5.1f}")

        track_ok = p_wm > 0.5 and is_detected(acc_wm) and p_orig < 0.5
        if not track_ok:
            print(f"   !! unexpected result for track {tid}")
        ok &= track_ok
        if args.save_dir:
            write_wav(args.save_dir / f"{tid:06d}_orig.wav", x)
            write_wav(args.save_dir / f"{tid:06d}_audioseal.wav", xw)

    print("\nOK: matches the expected behaviour" if ok else "\nFAILED: see the rows marked !!")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
