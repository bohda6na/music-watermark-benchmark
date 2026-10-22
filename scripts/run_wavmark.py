
import argparse
import time
from pathlib import Path

from attacks.noise_filtering import (
    gaussian_noise,
    lowpass_filter,
    highpass_filter,
    reverberation,
)
from methods.wavmark_method import WavMarkWatermarker
from scripts.common import (
    SR, MESSAGE, append_rows, bit_accuracy, bits_from_str,
    done_keys, find_track, is_detected, load_audio,
    read_selection, snr_db,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--fma-dir", type=Path, default=Path("fma_small"))
    parser.add_argument(
        "--out", type=Path,
        default=Path("results/results_wavmark.csv")
    )
    args = parser.parse_args()

    attacks = [
        ("none", "-", lambda x: x),
        ("gaussian_noise", "snr_db=30", lambda x: gaussian_noise(x, 30)),
        ("gaussian_noise", "snr_db=20", lambda x: gaussian_noise(x, 20)),
        ("gaussian_noise", "snr_db=10", lambda x: gaussian_noise(x, 10)),
        ("lowpass", "cutoff=3000", lambda x: lowpass_filter(x, SR)),
        ("highpass", "cutoff=300", lambda x: highpass_filter(x, SR)),
        ("reverberation", "decay=0.4,delay_ms=50,repeats=5",
         lambda x: reverberation(x, SR)),
    ]

    model = WavMarkWatermarker()
    message = bits_from_str(MESSAGE)
    tracks = read_selection()[:args.limit]
    done = done_keys(args.out)

    for i, (track_id, genre) in enumerate(tracks, 1):
        pending = [
            (name, params, fn)
            for name, params, fn in attacks
            if (str(track_id), name, params) not in done
        ]
        if not pending:
            continue

        start = time.time()
        path = find_track(track_id, None, args.fma_dir)
        original = load_audio(path)
        watermarked = model.embed(original, message, sr=SR)
        snr = snr_db(original, watermarked)

        for name, params, attack_fn in pending:
            attacked = attack_fn(watermarked.clip(-1, 1))
            decoded = model.detect(attacked, sr=SR)

            accuracy = (
                bit_accuracy(decoded, message)
                if decoded is not None else 0.0
            )

            row = {
                "method": "wavmark",
                "attack": name,
                "params": params,
                "genre": genre,
                "track_id": track_id,
                "detected": int(is_detected(accuracy)),
                "snr": round(snr, 3),
                "bit_acc": round(accuracy, 4),
                "detect_prob": "",
            }
            append_rows(args.out, [row])

            print(
                f"Track {track_id} | {name} | "
                f"bit_acc={accuracy:.3f} | detected={row['detected']}",
                flush=True
            )

        print(
            f"[{i}/{len(tracks)}] Completed in "
            f"{time.time() - start:.1f}s",
            flush=True
        )

    print(f"Results saved to {args.out}")


if __name__ == "__main__":
    main()
