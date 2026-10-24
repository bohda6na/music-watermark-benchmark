"""Midterm visualization of AudioSeal, audiowmark and WavMark results.

Run from the repository root:
    python scripts/plot_comparison.py
    python -m scripts.plot_comparison        # same

Uses only the results files listed in FILES (one per method).
Detection plots are based exclusively on `detected`; they do not use `bit_acc`.

Shared plots (01, 02, 04, 05) use every (attack, params) that all three methods were
tested with, in the order of the shared attack list (attacks.all_attacks). Attacks that
only some methods have (e.g. EnCodec, AudioSeal only) appear in the per-method plots (03).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so `attacks` imports when run as a plain script

from attacks import all_attacks  # noqa: E402

RESULTS = ROOT / "results"
OUT = ROOT / "plots" / "midterm"
OUT.mkdir(parents=True, exist_ok=True)

METHODS = ("audioseal", "audiowmark", "wavmark")
# Results file per method.
FILES = {
    "audioseal": "results_audioseal.csv",
    "audiowmark": "results_audiowmark.csv",
    "wavmark": "results_wavmark.csv",
}
COLORS = {"audioseal": "#3869C9", "audiowmark": "#E28A38", "wavmark": "#299B88"}

# Canonical order of all conditions (the control 'unwatermarked' is plotted separately).
ATTACK_ORDER = [("none", "-")] + [(a, p) for a, p, _ in all_attacks(include_neural=True)]

LABELS = {
    ("none", "-"): "No attack",
    ("gaussian_noise", "snr_db=30"): "Noise · 30 dB",
    ("gaussian_noise", "snr_db=20"): "Noise · 20 dB",
    ("gaussian_noise", "snr_db=10"): "Noise · 10 dB",
    ("lowpass", "cutoff=3000"): "Low-pass · 3 kHz",
    ("highpass", "cutoff=300"): "High-pass · 300 Hz",
    ("reverberation", "decay=0.4,delay_ms=50,repeats=5"): "Reverberation",
    ("crop", "keep50%"): "Crop · keep 50%",
}
PREFIX = {
    "mp3": "MP3",
    "aac": "AAC",
    "encodec": "EnCodec",
    "speed": "Speed",
    "time_stretch": "Time stretch",
    "pitch": "Pitch",
    "gain": "Gain",
}


def label(attack: str, params: str) -> str:
    if (attack, params) in LABELS:
        return LABELS[(attack, params)]
    p = params.replace("kbps", " kbps").replace("st", " st").replace("dB", " dB")
    return f"{PREFIX.get(attack, attack.replace('_', ' '))} · {p}"


def order_index(attack: str, params: str) -> int:
    key = (attack, params)
    return ATTACK_ORDER.index(key) if key in ATTACK_ORDER else len(ATTACK_ORDER)


def save(name: str) -> None:
    plt.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.savefig(OUT / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {name}.png / .pdf")


def load() -> pd.DataFrame:
    chunks = []
    for method in METHODS:
        path = RESULTS / FILES[method]
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}")
        d = pd.read_csv(path, dtype={"track_id": str, "params": str}, keep_default_na=False)
        required = {"method", "attack", "params", "genre", "track_id", "detected"}
        missing = required - set(d.columns)
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        d = d[d["method"].astype(str).str.lower() == method].copy()
        if d.empty:
            raise ValueError(f"{path.name}: no rows for method {method}")
        mapped = d["detected"].astype(str).str.strip().str.lower().map(
            {"1": 1, "0": 0, "true": 1, "false": 0, "1.0": 1, "0.0": 0}
        )
        if mapped.isna().any():
            raise ValueError(f"{path.name}: invalid detected values")
        d["detected"] = mapped.astype(int)
        key = ["method", "track_id", "attack", "params"]
        if d.duplicated(key).any():
            raise ValueError(f"{path.name}: duplicate track/attack entries")
        print(f"{method}: {len(d)} rows, {d.track_id.nunique()} tracks")
        chunks.append(d)
    return pd.concat(chunks, ignore_index=True)


def get_common(d: pd.DataFrame) -> pd.DataFrame:
    # Only comparable (attack, params) combos for all three methods.
    available = set.intersection(*(
        set(zip(s.attack, s.params)) for _, s in d.groupby("method")
    ))
    available.discard(("unwatermarked", "-"))
    selected = sorted(available, key=lambda k: order_index(*k))
    only_some = sorted(
        {k for k in zip(d.attack, d.params) if k not in available} - {("unwatermarked", "-")},
        key=lambda k: order_index(*k),
    )
    print(f"Shared conditions: {len(selected)}")
    if only_some:
        print("Not shared by all methods (per-method plots only):", only_some)
    if not selected:
        raise ValueError("No common attacks found")
    masks = pd.MultiIndex.from_frame(d[["attack", "params"]]).isin(selected)
    common = d.loc[masks].copy()
    common["label"] = [label(a, p) for a, p in zip(common.attack, common.params)]
    # Reproducible, fair comparison: require same track IDs per condition across methods.
    for attack, params in selected:
        sets = [set(common.loc[(common.method == m) & (common.attack == attack)
                               & (common.params == params), "track_id"]) for m in METHODS]
        if len(set.union(*sets)) != len(set.intersection(*sets)):
            raise ValueError(f"Different tracks across methods for {attack} / {params}")
    return common


def comparison_table(common: pd.DataFrame) -> pd.DataFrame:
    rates = common.groupby(["label", "method"])["detected"].mean().mul(100).unstack()
    keys = sorted(set(zip(common.attack, common.params)), key=lambda k: order_index(*k))
    order = [label(*key) for key in keys if label(*key) in rates.index]
    return rates.reindex(order)[list(METHODS)]


def plot_grouped(table: pd.DataFrame) -> None:
    n = len(table)
    fig, ax = plt.subplots(figsize=(max(12.2, 0.62 * n + 2), 5.9))
    x = np.arange(n)
    w = 0.26
    for i, m in enumerate(METHODS):
        bars = ax.bar(x + (i - 1) * w, table[m], width=w, label=m,
                      color=COLORS[m])
        for bar in bars:
            height = bar.get_height()
            if pd.notna(height):
                ax.annotate(f"{height:.0f}", (bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 2), textcoords="offset points", ha="center",
                            fontsize=6.5 if n > 10 else 7.5)
    ax.set(title=f"Robustness comparison · {n} shared conditions",
           ylabel="Message decoded (≥14/16 bits), %", ylim=(0, 112))
    ax.set_xticks(x, table.index, rotation=40 if n > 10 else 25, ha="right")
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=.17)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save("01_shared_comparison")


def plot_heatmap(table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, max(5.4, 0.36 * len(table) + 1.5)))
    arr = table.to_numpy()
    im = ax.imshow(arr, vmin=0, vmax=100, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(np.arange(len(METHODS)), METHODS)
    ax.set_yticks(np.arange(len(table)), table.index)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            value = arr[i, j]
            if np.isfinite(value):
                ax.text(j, i, f"{value:.1f}%", ha="center", va="center",
                        fontsize=9, color="white" if value >= 65 else "black")
    ax.set_title("Detection rate · same tracks and attacks")
    fig.colorbar(im, ax=ax, label="Detection rate (%)")
    fig.tight_layout()
    save("02_shared_heatmap")


def plot_individual(d: pd.DataFrame, method: str) -> None:
    # EnCodec was run only for AudioSeal, so it is left out to keep the plots comparable.
    part = d[(d.method == method) & ~d.attack.isin(["unwatermarked", "encodec"])].copy()
    summary = part.groupby(["attack", "params"], sort=True)["detected"].agg(["mean", "size"]).reset_index()
    summary["display"] = [label(a, p) for a, p in zip(summary.attack, summary.params)]
    summary["rate"] = summary["mean"] * 100
    summary["order"] = [order_index(a, p) for a, p in zip(summary.attack, summary.params)]
    summary = summary.sort_values(["order", "attack", "params"])
    fig, ax = plt.subplots(figsize=(11.5, max(5, 0.34 * len(summary) + 1.6)))
    y = np.arange(len(summary))
    bars = ax.barh(y, summary.rate, color=COLORS[method], height=0.73)
    ax.set_yticks(y, summary.display, fontsize=8.4)
    ax.invert_yaxis()
    ax.set_xlim(0, 118)
    for bar, rate in zip(bars, summary.rate):
        ax.text(rate + 1.2, bar.get_y() + bar.get_height()/2, f"{rate:.1f}%",
                va="center", fontsize=8)
    ax.set(title=f"{method} · all tested attacks", xlabel="Detection rate (%)")
    ax.grid(axis="x", alpha=.17)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(f"03_{method}_all_attacks")


def plot_genres(common: pd.DataFrame) -> None:
    # Shared attacks only, excluding baseline; unwatermarked is never included.
    attacked = common[~common.attack.isin(["none", "unwatermarked"])]
    n_attacks = attacked[["attack", "params"]].drop_duplicates().shape[0]
    g = attacked.groupby(["genre", "method"])["detected"].mean().mul(100).unstack()
    g = g.reindex(columns=list(METHODS)).sort_index()
    if g.empty:
        return
    fig, ax = plt.subplots(figsize=(11.8, 5.6))
    x = np.arange(len(g))
    w = .26
    for i, method in enumerate(METHODS):
        ax.bar(x + (i-1)*w, g[method], width=w, color=COLORS[method], label=method)
    ax.set_xticks(x, g.index, rotation=25, ha="right")
    ax.set(title=f"Detection rate by genre · {n_attacks} shared attacks (baseline excluded)",
           ylabel="Detection rate (%)", ylim=(0, 105))
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=.17)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save("04_genres_shared_attacks")


def plot_noise(common: pd.DataFrame) -> None:
    noise = common[common.attack == "gaussian_noise"].copy()
    if noise.empty:
        return
    noise["snr_db"] = noise.params.str.extract(r"snr_db=(\d+)")[0].astype(int)
    rates = noise.groupby(["snr_db", "method"])["detected"].mean().mul(100).unstack()
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for method in METHODS:
        ax.plot(rates.index, rates[method], "o-", lw=2.4, markersize=7,
                label=method, color=COLORS[method])
    ax.set(title="Robustness to Gaussian noise", xlabel="Signal-to-noise ratio (dB)",
           ylabel="Detection rate (%)", ylim=(-3, 103), xticks=sorted(rates.index))
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    fig.tight_layout()
    save("05_noise_snr")


def plot_controls(d: pd.DataFrame) -> None:
    ctl = d[d.attack == "unwatermarked"]
    if ctl.empty:
        print("No unwatermarked controls found; skipping controls graph")
        return
    summary = ctl.groupby("method")["detected"].agg(["mean", "size"])
    fig, ax = plt.subplots(figsize=(6.5, 4.1))
    names = list(summary.index)
    values = summary["mean"] * 100
    bars = ax.bar(names, values, color=[COLORS[m] for m in names], width=.58)
    for bar, n in zip(bars, summary["size"]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.8,
                f"{bar.get_height():.1f}% (n={n})", ha="center", fontsize=9)
    ax.set(title="Unwatermarked controls · false message reads",
           ylabel="Message read (%)", ylim=(0, max(10, float(values.max())*1.5+5)))
    ax.grid(axis="y", alpha=.15)
    fig.tight_layout()
    save("06_unwatermarked_controls")
    missing = [m for m in METHODS if m not in names]
    if missing:
        print(f"Note: no unwatermarked control rows for {missing}; no bar shown for them.")


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    df = load()
    common = get_common(df)
    table = comparison_table(common)
    table.round(3).to_csv(OUT / "shared_comparison_percent.csv")
    print("\nShared detection rates (%):\n", table.round(1).to_string(), "\n")
    plot_grouped(table)
    plot_heatmap(table)
    for method in METHODS:
        plot_individual(df, method)
    plot_genres(common)
    plot_noise(common)
    plot_controls(df)
    print(f"\nDone. Charts in {OUT}")
    print("Note: all charts use `detected`, not `bit_acc` or sensitivity data.")


if __name__ == "__main__":
    main()
