"""Run AudioSeal on the 80 selected tracks: no attack + compression attacks -> CSV.

For each track: embed the shared 16-bit message, compute SNR(original, watermarked),
then detect after every attack. One CSV row per (track, attack, params):

    method, attack, params, genre, track_id, detected, snr, bit_acc, detect_prob

- `snr` is always original vs watermarked (before the attack), as in data/README.md;
- `detected` = bit_acc >= 14/16; `detect_prob` is AudioSeal's own detector output;
- attack "unwatermarked" runs detection on the original track (false-positive check).

The script appends to the CSV and skips rows that already exist, so it can be resumed.

    python -m scripts.run_audioseal --wav-dir data/wav --out results/results_audioseal.csv
    python -m scripts.run_audioseal --fma-dir data/raw/fma_small --neural   # + EnCodec
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from attacks.compression import compression_attacks
from methods.audioseal_method import AudioSealWatermarker
from scripts.common import (
    MESSAGE, append_rows, bit_accuracy, bits_from_str, done_keys, find_track,
    is_detected, load_audio, read_selection, snr_db, write_wav,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wav-dir", type=Path, help="folder with mono 44.1 kHz WAVs (000002.wav)")
    p.add_argument("--fma-dir", type=Path, help="fma_small folder with the original mp3 files")
    p.add_argument("--out", type=Path, default=Path("results/results_audioseal.csv"))
    p.add_argument("--neural", action="store_true", help="also run the EnCodec attack (pip install encodec)")
    p.add_argument("--no-negative", action="store_true", help="skip the 'unwatermarked' control row")
    p.add_argument("--save-wm-dir", type=Path, help="optionally save watermarked WAVs here")
    p.add_argument("--limit", type=int, help="only the first N tracks (for a quick test)")
    p.add_argument("--device", default=None)
    args = p.parse_args()
    if not args.wav_dir and not args.fma_dir:
        p.error("give --wav-dir or --fma-dir")

    attacks = [("none", "-", lambda x: x)] + compression_attacks(include_neural=args.neural)
    tracks = read_selection()[: args.limit]
    message = bits_from_str(MESSAGE)
    done = done_keys(args.out)
    model = AudioSealWatermarker(args.device)
    if args.save_wm_dir:
        args.save_wm_dir.mkdir(parents=True, exist_ok=True)
    print(f"device={model.device}  tracks={len(tracks)}  attacks={len(attacks)}  out={args.out}")

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
            write_wav(args.save_wm_dir / f"{tid:06d}_audioseal.wav", xw)

        def row(attack: str, params: str, prob: float, bits) -> dict:
            acc = bit_accuracy(bits, message)
            return {"method": "audioseal", "attack": attack, "params": params, "genre": genre,
                    "track_id": tid, "detected": int(is_detected(acc)), "snr": round(snr, 3),
                    "bit_acc": round(acc, 4), "detect_prob": round(prob, 4)}

        rows = []
        if need_negative:
            rows.append(row("unwatermarked", "-", *model.detect(x)))
        for attack, params, fn in todo:
            # attacks get the clipped signal, exactly what would be saved to a file
            rows.append(row(attack, params, *model.detect(fn(xw.clip(-1, 1)))))
        append_rows(args.out, rows)

        summary = " ".join(f"{r['attack']}/{r['params']}={r['detected']}" for r in rows)
        print(f"[{i}/{len(tracks)}] {tid} {genre} snr={snr:.1f}dB {time.time() - t0:.1f}s  {summary}")

    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
