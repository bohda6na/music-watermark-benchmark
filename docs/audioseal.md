# AudioSeal and compression attacks

Owner: Iryna Svyrydenko.

## Files

- `methods/audioseal_method.py` – AudioSeal wrapper: `embed(x, message)`, `detect(y)`.
- `attacks/compression.py` – MP3 and AAC at 128 / 64 / 32 kbps (ffmpeg), optional EnCodec
  neural codec at 24 / 12 / 6 / 3 / 1.5 kbps. Each attack takes and returns mono 44.1 kHz audio
  of the same length, so the other methods can use them too.
- `scripts/common.py` – shared helpers: audio loading, SNR, bit accuracy, the shared
  16-bit message, CSV writing.
- `scripts/audioseal_smoke_test.py` – embed/detect check on 5 tracks (5 genres).
- `scripts/run_audioseal.py` – full run on the 80 tracks → `results/results_audioseal.csv`.

## How to run

    pip install -r requirements-audioseal.txt
    python -m scripts.audioseal_smoke_test --wav-dir <wav-folder>
    python -m scripts.run_audioseal --wav-dir <wav-folder> --out results/results_audioseal.csv
    python -m scripts.run_audioseal --wav-dir <wav-folder> --neural   # also EnCodec

`--fma-dir <fma_small>` can be used instead of `--wav-dir`: the mp3 files are then decoded
to mono 44.1 kHz on the fly. `--limit N` runs only the first N tracks.
The full run appends to the CSV and skips finished rows, so it can be resumed.

## Implementation notes

- **Sample rate.** AudioSeal models are trained at 16 kHz, and since version 0.2 the
  library does not resample (the `sample_rate` argument is ignored). The wrapper resamples
  the track to 16 kHz, computes the watermark, upsamples the watermark to 44.1 kHz and adds it
  to the original. Detection resamples to 16 kHz first.
- **torch.compile is disabled** (`NO_TORCH_COMPILE=1`): it needs a C++ compiler on Windows
  and does not speed up a run this small.
- **Detection.** `detected = bit_acc >= 14/16`, same rule as for the other methods.
  `detect_prob` (AudioSeal's own detector, share of frames with p > 0.5) is saved as an
  extra column.
- **Control row.** `attack = unwatermarked` runs detection on the original track. It shows
  the false-positive rate: bit accuracy there should be around 50% and `detect_prob` near 0.
- **SNR** is always original vs watermarked, before any attack.
- **Codec alignment.** Checked by cross-correlation: after MP3 / AAC / EnCodec round trips the
  signal has no time shift and the same length as the input.
