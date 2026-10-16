# Robust Music Watermarking: Extended Benchmark

Semester project, course "Artificial Intelligence", Ukrainian Catholic University (2026).

Team: Iryna Svyrydenko, Lili Alania, Bohdana Zubrytska. Mentor: Olesia Omelchuk.

## Problem

Audio watermarking embeds an inaudible identifier into a signal. It is used to label
AI-generated music and to protect creators' rights. Most existing methods were built and
evaluated on speech, and their robustness is usually tested under lab conditions rather
than the transformations a track meets in practice. This project builds a benchmark
focused on music across genres and compares several watermarking methods under the
same attacks.

## Data

- Dataset: FMA-small (8,000 tracks, 30 s each, 8 balanced genres).
  Source: https://github.com/mdeff/fma
- Test subset: the first 10 tracks (by sorted `track_id`) of each of the 8 genres,
  80 tracks in total. The list is in `data/selected_80.csv`.
- Audio files are not stored in this repository. See `data/README.md` for licences
  and download links.

## Methods

All methods embed the same 16-bit message, so the results are comparable.

- audiowmark (classical, spread spectrum). Owner: Bohdana
- AudioSeal (neural). Owner: Iryna
- WavMark (neural). Owner: Lili

## Attacks

My part is the time and dynamics group, implemented in `attacks/attacks.py`.
The parameters are the same for every method:

- Speed change (tempo and pitch together): 0.9x, 0.95x, 1.05x, 1.1x
- Time stretch (pitch preserved): 0.9x, 0.95x, 1.05x, 1.1x
- Pitch shift: -2, -1, +1, +2 semitones
- Gain: -6 dB and +6 dB (with clipping)
- Crop: keep the first 50% of the track

Other attack groups (compression, noise, filtering) are implemented by teammates.

## Metrics

- Robustness: the share of tracks where the watermark is still detected after the attack.
  A watermark counts as detected when bit accuracy is at least 14/16 (87.5%)
  for the 16-bit message.
- Audio quality: SNR in dB between the original and the watermarked track:
  `SNR = 10 * log10( sum(x^2) / sum((x - x_w)^2) )`.
- Details and thresholds: `docs/metrics.md`.

## Results

Result files are CSV files in `results/` with the columns
`method, attack, params, genre, track_id, detected, snr, bit_acc`.

Preliminary results for audiowmark: [fill in after the full run finishes, for example
the detection rate for each attack as a short list]

This is a pilot sample of 80 tracks (10 per genre), so genre-level conclusions
are preliminary.

## How to run

Tested on Linux (Google Colab). audiowmark must be installed first
(https://github.com/swesterfeld/audiowmark).

    pip install -r requirements.txt
    python -m scripts.run_audiowmark --wav-dir <path-to-wav-folder> --out results/results_audiowmark.csv

WAV files are mono, 44.1 kHz, converted from the FMA mp3 files with ffmpeg.
The script appends to the CSV and skips rows that are already done, so an interrupted
run can be resumed.

## AI usage

- Tool: [Claude (Anthropic)]
- Used for: [guidance on setting up the Colab environment, drafting the attack and run
  scripts, structuring the repository and documentation]
- Verification: [I ran every script myself; checked embed and detect on a single track;
  confirmed that identity attacks (speed 1.0, time stretch 1.0, pitch 0) preserve the
  watermark; checked the output CSV for row counts and duplicates; I can explain
  every line of my code]

## Contribution statement

- Iryna Svyrydenko: [...]
- Lili Alania: [...]
- Bohdana Zubrytska: third open-source method (audiowmark), time and dynamics attacks,
  metrics and thresholds, runs on the 80-track subset.


## Licenses and third-party material

Data: FMA, metadata under CC BY 4.0, audio under artist-chosen Creative Commons licences.
audiowmark: [check its licence and note it here]