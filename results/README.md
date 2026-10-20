# Results: audiowmark on FMA-small

Setup: audiowmark, 16-bit message (`a5c3`), default strength 10, 80 tracks
(10 per genre), mono 44.1 kHz WAV. A message counts as **detected** if
bit accuracy >= 14/16 (0.875).

Files (columns: `method, attack, params, genre, track_id, detected, snr, bit_acc`):
- `results_audiowmark.csv`: main run, 80 tracks x 16 variants = 1280 rows;
- `results_audiowmark_detect_speed.csv`: extra run with `--detect-speed`, 80 x 2 = 160 rows.

Reproduce the numbers below (needs only the CSV files, no audio):
```
python scripts/summarize_results.py results/results_audiowmark.csv
python scripts/summarize_results.py results/results_audiowmark_detect_speed.csv
```

## Robustness (share of 80 tracks with the message detected)

| Attack | Parameters | Detection rate |
| ------ | ---------- | -------------- |
| none (baseline) | - | 1.0 |
| gain | -6 dB, +6 dB | 1.0 |
| crop | keep first 50% | 1.0 |
| speed | 0.9x, 0.95x, 1.05x, 1.1x | 0.0 |
| time_stretch | 0.9x, 0.95x, 1.05x, 1.1x | 0.0 |
| pitch | -2, -1, +1, +2 semitones | 0.0 |

## Extra experiment: `--detect-speed` (speed attack only)

| Method | Speed | Detection rate | Mean bit accuracy |
| ------ | ----- | -------------- | ----------------- |
| audiowmark | 0.9x | 0.0 | - |
| audiowmark | 1.1x | 0.0 | - |
| audiowmark+detect-speed | 0.9x | 1.0 | 1.0 |
| audiowmark+detect-speed | 1.1x | 1.0 | 1.0 |

The main run keeps this option **off**, because AudioSeal and WavMark have no such mode and
the comparison must use equal conditions.

## Audio quality (SNR after embedding, no attack)

- All 80 tracks: mean **31.0 dB**, range 25.5-51.0 dB.
- Genre means range from 29.9 dB (Hip-Hop) to 33.8 dB (Electronic).

## Limitations
- 80 tracks, 10 per genre: genre-level conclusions are preliminary. For every attack tested so
  far the detection rate is 0 or 1 in all genres, so genres cannot be compared yet.
- One method, one message (`a5c3`), one embedding strength (default).
- `--detect-speed` was tested on all 80 tracks only for speed 0.9x and 1.1x. For
  `time_stretch` and `pitch` it was tried on one track and did not help.
- SNR measures how much the signal changed, not how audible the change is. We ran no
  listening tests.
- The false-positive check (reading a message from an unmarked file) was done on one track only.
- The source files were already mp3, converted to WAV.