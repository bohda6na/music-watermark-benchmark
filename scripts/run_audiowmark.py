"""Run audiowmark on the 80 selected tracks: no attack + time/dynamics attacks -> CSV.

One CSV row per (track, attack, params), same columns as the other methods:

    method, attack, params, genre, track_id, detected, snr, bit_acc, detect_prob

- `snr` is original vs watermarked (before the attack);
- `detected` = bit_acc >= 14/16; if audiowmark finds no pattern, detected=0 and bit_acc is empty;
- `detect_prob` is empty (audiowmark has no probability output);
- attack "unwatermarked" runs detection on the original track (false-positive check);
- `--detect-speed` turns on audiowmark's speed detection (a separate experiment, method name
  "audiowmark+detect-speed"), it is NOT part of the main comparison.

The script appends to the CSV and skips rows that already exist, so it can be resumed.

    python -m scripts.run_audiowmark --wav-dir data/wav --out results/results_audiowmark.csv
    python -m scripts.run_audiowmark --wav-dir data/wav --detect-speed --attacks speed \\
        --params 0.9x 1.1x --out results/results_audiowmark_detect_speed.csv
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from attacks.time_dynamics import time_dynamics_attacks
from methods.audiowmark_method import AudiowmarkWatermarker
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
)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--wav-dir", type=Path, help="folder with mono 44.1 kHz WAVs (000002.wav)")
    p.add_argument("--fma-dir", type=Path, help="fma_small folder with the original mp3 files")
    p.add_argument("--out", type=Path, default=Path("results/results_audiowmark.csv"))
    p.add_argument("--detect-speed", action="store_true", help="enable audiowmark --detect-speed")
    p.add_argument("--attacks", nargs="*", help="run only these attack names (e.g. speed)")
    p.add_argument("--params", nargs="*", help="run only these params (e.g. 0.9x 1.1x)")
    p.add_argument(
        "--no-negative", action="store_true", help="skip the 'unwatermarked' control row"
    )
    p.add_argument("--limit", type=int, help="only the first N tracks (for a quick test)")
    args = p.parse_args()
    if not args.wav_dir and not args.fma_dir:
        p.error("give --wav-dir or --fma-dir")

    attacks = [("none", "-", lambda x: x)] + time_dynamics_attacks()
    if args.attacks:
        attacks = [a for a in attacks if a[0] in args.attacks]
    if args.params:
        attacks = [a for a in attacks if a[1] in args.params]

    extra = ("--detect-speed",) if args.detect_speed else ()
    method_name = "audiowmark+detect-speed" if args.detect_speed else "audiowmark"

    tracks = read_selection()[: args.limit]
    message = bits_from_str(MESSAGE)
    done = done_keys(args.out)
    model = AudiowmarkWatermarker()
    print(f"method={method_name}  tracks={len(tracks)}  attacks={len(attacks)}  out={args.out}")

    for i, (tid, genre) in enumerate(tracks, 1):
        todo = [a for a in attacks if (str(tid), a[0], a[1]) not in done]
        need_negative = not args.no_negative and (str(tid), "unwatermarked", "-") not in done
        if not todo and not need_negative:
            continue

        t0 = time.time()
        x = load_audio(find_track(tid, args.wav_dir, args.fma_dir))
        xw = model.embed(x, message)
        snr = snr_db(x, xw)

        def row(attack: str, params: str, bits) -> dict:
            acc = bit_accuracy(bits, message) if bits is not None else None
            return {
                "method": method_name,
                "attack": attack,
                "params": params,
                "genre": genre,
                "track_id": tid,
                "detected": int(acc is not None and is_detected(acc)),
                "snr": round(snr, 3),
                "bit_acc": "" if acc is None else round(acc, 4),
                "detect_prob": "",
            }

        rows = []
        if need_negative:
            rows.append(row("unwatermarked", "-", model.detect(x, extra=extra)))
        for attack, params, fn in todo:
            # attacks get the clipped signal, exactly what would be saved to a file
            rows.append(row(attack, params, model.detect(fn(xw.clip(-1, 1)), extra=extra)))
        append_rows(args.out, rows)

        summary = " ".join(f"{r['attack']}/{r['params']}={r['detected']}" for r in rows)
        print(f"[{i}/{len(tracks)}] {tid} {genre} snr={snr:.1f}dB {time.time() - t0:.0f}s  {summary}")

    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()