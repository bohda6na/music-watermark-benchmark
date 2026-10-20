"""Check a results CSV and print the main numbers.

Usage:
    python scripts/summarize_results.py [path/to/results.csv]

Expected CSV columns: method, attack, params, genre, track_id, detected, snr, bit_acc
"""
import sys

import pandas as pd

DEFAULT_PATH = "results/results_audiowmark.csv"


def main(path):
    # keep_default_na=False: empty `params` (attack "none") and empty `bit_acc`
    # (message not found) stay as empty strings instead of becoming NaN.
    d = pd.read_csv(path, keep_default_na=False)

    # "detected" is saved as True/False; compare as text to be safe.
    d["detected"] = d["detected"].astype(str).eq("True")

    # 1. File integrity
    print(f"file: {path}")
    print(f"rows: {len(d)}, tracks: {d['track_id'].nunique()}, "
          f"genres: {d['genre'].nunique()}")
    print("rows per track (count of tracks):")
    print(d.groupby("track_id").size().value_counts().to_string())
    n_dup = d.duplicated(["method", "track_id", "attack", "params"]).sum()
    print(f"duplicates: {n_dup}")

    # 2. Robustness: share of tracks where the message was detected
    print("\ndetection rate by attack:")
    print(d.groupby(["method", "attack"])["detected"].mean().round(2).to_string())

    print("\ndetection rate by attack and parameter:")
    print(d.groupby(["method", "attack", "params"])["detected"].mean().round(2).to_string())

    # 3. Audio quality: SNR after embedding (no attack)
    s = d[d["attack"] == "none"].copy()
    if len(s):
        s["snr"] = s["snr"].astype(float)
        print("\nSNR after embedding, no attack (dB):")
        print(s.groupby("genre")["snr"].agg(["mean", "median", "min", "max"]).round(1).to_string())
        print(f"all tracks: mean {s['snr'].mean():.1f}, "
              f"min {s['snr'].min():.1f}, max {s['snr'].max():.1f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH)