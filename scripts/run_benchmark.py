"""Run one watermarking method on the 80 selected tracks under all attacks -> CSV.

Same loop for every method: load track -> embed the shared 16-bit message -> SNR ->
apply each attack -> detect -> one CSV row per (track, attack, params):

    method, attack, params, genre, track_id, detected, snr, bit_acc, detect_prob

- `snr` is original vs watermarked (before the attack);
- `detected` = bit_acc >= 14/16; if the method finds no message, detected=0 and bit_acc is empty;
- `detect_prob` is the method's own detector output (AudioSeal only, empty for the others);
- attack "unwatermarked" runs detection on the original track (false-positive check);
- attacks come from `attacks.all_attacks()`, so every method gets the same ones.

The script appends to the CSV and skips rows that already exist, so it can be resumed.

    python -m scripts.run_benchmark --method audioseal --wav-dir data/wav
    python -m scripts.run_benchmark --method audioseal --wav-dir data/wav --neural  # + EnCodec
    python -m scripts.run_benchmark --method wavmark --wav-dir data/wav --limit 2   # quick test
    python -m scripts.run_benchmark --method audiowmark --wav-dir data/wav --detect-speed \\
        --attacks speed --params 0.9x 1.1x --out results/results_audiowmark_detect_speed.csv

Default output: results/results_<method>.csv.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from attacks import all_attacks
from scripts.common import (
    MESSAGE,
    append_rows,
    bit_accuracy,
    bits_from_str,
    done_keys,
    find_track,
    is_detected,
    load_audio,
    read_selection,
    snr_db,
    write_wav,
)

METHODS = ("audioseal", "audiowmark", "wavmark")


@dataclass
class Method:
    """A watermarking method with a common interface.

    embed(x, message) -> watermarked x (same length, 44.1 kHz)
    detect(y) -> (detect_prob or None, decoded bits or None)
    """

    label: str
    embed: Callable[[np.ndarray, np.ndarray], np.ndarray]
    detect: Callable[[np.ndarray], tuple[float | None, np.ndarray | None]]
    device: str = "-"


def load_method(name: str, device: str | None = None, detect_speed: bool = False) -> Method:
    """Create a method. Imports are done here, so each method needs only its own packages."""
    if detect_speed and name != "audiowmark":
        raise ValueError("--detect-speed works only with --method audiowmark")

    if name == "audioseal":
        from methods.audioseal_method import AudioSealWatermarker

        m = AudioSealWatermarker(device)
        return Method("audioseal", m.embed, m.detect, m.device)

    if name == "audiowmark":
        from methods.audiowmark_method import AudiowmarkWatermarker

        m = AudiowmarkWatermarker()
        extra = ("--detect-speed",) if detect_speed else ()
        label = "audiowmark+detect-speed" if detect_speed else "audiowmark"
        return Method(label, m.embed, lambda y: (None, m.detect(y, extra=extra)))

    if name == "wavmark":
        from methods.wavmark_method import WavMarkWatermarker

        m = WavMarkWatermarker(device)
        return Method("wavmark", m.embed, lambda y: (None, m.detect(y)), m.device)

    raise ValueError(f"unknown method {name!r}, choose from {METHODS}")


def make_row(method, attack, params, genre, tid, snr, prob, bits, message) -> dict:
    acc = None if bits is None else bit_accuracy(bits, message)
    return {
        "method": method,
        "attack": attack,
        "params": params,
        "genre": genre,
        "track_id": tid,
        "detected": int(acc is not None and is_detected(acc)),
        "snr": round(snr, 3),
        "bit_acc": "" if acc is None else round(acc, 4),
        "detect_prob": "" if prob is None else round(float(prob), 4),
    }


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--method", required=True, choices=METHODS)
    p.add_argument("--wav-dir", type=Path, help="folder with mono 44.1 kHz WAVs (000002.wav)")
    p.add_argument("--fma-dir", type=Path, help="fma_small folder with the original mp3 files")
    p.add_argument("--out", type=Path, help="CSV file (default: results/results_<method>.csv)")
    p.add_argument("--neural", action="store_true", help="also run the EnCodec attack")
    p.add_argument("--detect-speed", action="store_true", help="audiowmark --detect-speed")
    p.add_argument("--attacks", nargs="*", help="run only these attack names (e.g. speed)")
    p.add_argument("--params", nargs="*", help="run only these params (e.g. 0.9x 1.1x)")
    p.add_argument(
        "--no-negative", action="store_true", help="skip the 'unwatermarked' control row"
    )
    p.add_argument("--save-wm-dir", type=Path, help="optionally save watermarked WAVs here")
    p.add_argument("--limit", type=int, help="only the first N tracks (for a quick test)")
    p.add_argument("--device", default=None, help="cpu or cuda (neural methods)")
    args = p.parse_args(argv)
    if not args.wav_dir and not args.fma_dir:
        p.error("give --wav-dir or --fma-dir")

    attacks = all_attacks(include_neural=args.neural)
    if args.attacks:
        attacks = [a for a in attacks if a[0] in args.attacks]
    if args.params:
        attacks = [a for a in attacks if a[1] in args.params]

    model = load_method(args.method, args.device, args.detect_speed)
    out = args.out or Path(f"results/results_{args.method}.csv")
    tracks = read_selection()[: args.limit]
    message = bits_from_str(MESSAGE)
    done = done_keys(out)
    if args.save_wm_dir:
        args.save_wm_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"method={model.label}  device={model.device}  tracks={len(tracks)}  "
        f"attacks={len(attacks)}  out={out}"
    )

    for i, (tid, genre) in enumerate(tracks, 1):
        todo = [a for a in attacks if (str(tid), a[0], a[1]) not in done]
        need_negative = not args.no_negative and (str(tid), "unwatermarked", "-") not in done
        if not todo and not need_negative:
            continue

        t0 = time.time()
        x = load_audio(find_track(tid, args.wav_dir, args.fma_dir))
        xw = model.embed(x, message)
        snr = snr_db(x, xw)
        if args.save_wm_dir:
            write_wav(args.save_wm_dir / f"{tid:06d}_{args.method}.wav", xw)

        def row(attack: str, params: str, y: np.ndarray) -> dict:
            prob, bits = model.detect(y)
            return make_row(model.label, attack, params, genre, tid, snr, prob, bits, message)

        rows = []
        if need_negative:
            rows.append(row("unwatermarked", "-", x))
        for attack, params, fn in todo:
            # attacks get the clipped signal, exactly what would be saved to a file
            rows.append(row(attack, params, fn(xw.clip(-1, 1))))
        append_rows(out, rows)

        summary = " ".join(f"{r['attack']}/{r['params']}={r['detected']}" for r in rows)
        elapsed = time.time() - t0
        print(f"[{i}/{len(tracks)}] {tid} {genre} snr={snr:.1f}dB {elapsed:.1f}s  {summary}")

    print(f"done -> {out}")


if __name__ == "__main__":
    main()
