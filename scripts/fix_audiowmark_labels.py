"""One-off fix: bring the old audiowmark CSVs to the label format used by the run scripts.

Old notebook run -> current format (same as results_audioseal.csv):
    params:   0.9 -> 0.9x, -1 -> -1st, 6 -> +6dB, 0.5 -> keep50%, empty -> "-"
    detected: True/False -> 1/0
    new empty column detect_prob (audiowmark has no probability output)

Run once from the repo root:  python scripts/fix_audiowmark_labels.py
Running it again is safe: files that already have detect_prob are skipped.
"""

from pathlib import Path

import pandas as pd

FMT = {
    "none": lambda p: "-",
    "speed": lambda p: f"{float(p):g}x",
    "time_stretch": lambda p: f"{float(p):g}x",
    "pitch": lambda p: f"{int(float(p)):+d}st",
    "gain": lambda p: f"{int(float(p)):+d}dB",
    "crop": lambda p: f"keep{int(float(p) * 100)}%",
}

for name in ("results_audiowmark.csv", "results_audiowmark_detect_speed.csv"):
    path = Path("results") / name
    d = pd.read_csv(path, keep_default_na=False, dtype=str)
    if "detect_prob" in d.columns:
        print(f"{name}: already fixed, skipped")
        continue
    d["params"] = [FMT[a](p) for a, p in zip(d["attack"], d["params"])]
    d["detected"] = d["detected"].map({"True": "1", "False": "0"})
    d["detect_prob"] = ""
    d.to_csv(path, index=False)
    print(f"{name}: {len(d)} rows")