# Results: audiowmark on FMA-small

Setup: audiowmark, 16-bit message (`a5c3`), default strength 10, 80 tracks
(10 per genre), mono 44.1 kHz WAV. A message counts as **detected** if
bit accuracy >= 14/16 (0.875).

Files (columns: `method, attack, params, genre, track_id, detected, snr, bit_acc, detect_prob`;
`detect_prob` is empty for audiowmark):
- `results_audiowmark.csv`: main run, 80 tracks x 29 rows = 2320 rows (no attack, 27 attack
  variants and one unwatermarked control);
- `results_audiowmark_detect_speed.csv`: extra run with `--detect-speed`, 80 x 3 = 240 rows
  (speed 0.9x and 1.1x, plus the unwatermarked control with the option switched on).

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
---

# Results: AudioSeal on FMA-small

Setup: AudioSeal (`audioseal_wm_16bits` generator + `audioseal_detector_16bits`), same
16-bit message (`a5c3`), same 80 tracks. The model works at 16 kHz: the watermark is made at
16 kHz, upsampled and added to the original 44.1 kHz track (see `docs/audioseal.md`).

File: `results_audioseal.csv`, 80 tracks x 34 rows = 2720 rows (no attack, 33 attack
variants, and one unwatermarked control). Same columns as above plus `detect_prob`.

AudioSeal gives two outputs, so the table has two columns:
- **message read**: at least 14 of 16 bits correct, the shared team criterion (`detected` column);
- **watermark found**: AudioSeal's own detector, probability > 0.5 (`detect_prob` column).

Reproduce (needs only the CSV file):
```
python scripts/summarize_results.py results/results_audioseal.csv
```
Run (resumable, uses an NVIDIA GPU if the CUDA build of torch is installed):
```
python -m scripts.run_audioseal --wav-dir <wav-folder> --neural --out results/results_audioseal.csv
```

## Robustness (share of 80 tracks)

| Attack | Parameters | Message read | Watermark found | Mean correct bits |
| ------ | ---------- | ------------ | --------------- | ----------------- |
| none (baseline) | - | 0.64 | 1.00 | 14.2 |
| mp3 | 128 / 64 / 32 kbps | 0.63 / 0.60 / 0.59 | 1.00 / 1.00 / 1.00 | 14.1 / 13.9 / 13.9 |
| aac | 128 / 64 / 32 kbps | 0.61 / 0.65 / 0.50 | 1.00 / 1.00 / 1.00 | 14.0 / 13.9 / 13.7 |
| encodec | 24 / 12 kbps | 0.39 / 0.28 | 0.99 / 0.99 | 13.2 / 12.4 |
| encodec | 6 / 3 / 1.5 kbps | 0.01 / 0.00 / 0.00 | 0.30 / 0.16 / 0.03 | 10.1 / 7.2 / 6.9 |
| gain | -6 dB / +6 dB | 0.60 / 0.59 | 1.00 / 1.00 | 13.5 / 13.7 |
| crop | keep first 50% | 0.84 | 1.00 | 15.0 |
| speed | 0.9x, 0.95x, 1.05x, 1.1x | 0.00 | 0.00-0.01 | 6.9-9.1 |
| pitch | -2, -1, +1, +2 semitones | 0.00 | 0.00 | 7.0-7.4 |
| time_stretch | 0.9x / 0.95x / 1.05x / 1.1x | 0.05 / 0.08 / 0.40 / 0.29 | 0.00 | 9.3 / 9.5 / 12.6 / 11.9 |
| gaussian_noise | SNR 30 / 20 / 10 dB | 0.43 / 0.33 / 0.18 | 1.00 / 1.00 / 0.96 | 13.3 / 12.6 / 12.3 |
| lowpass | cutoff 3 kHz | 0.64 | 1.00 | 14.1 |
| highpass | cutoff 300 Hz | 0.70 | 1.00 | 14.1 |
| reverberation | decay 0.4, delay 50 ms, 5 echoes | 0.64 | 1.00 | 14.0 |
| unwatermarked (control) | - | 0.00 | 0.00 | 7.7 |

## Noise and filtering by genre (message read, 10 tracks each)

The watermark is found in all tracks of every genre for these attacks, except Gaussian noise
at 10 dB (0.9 in Electronic, Experimental and Pop).

| Genre | none | noise 30 dB | noise 20 dB | noise 10 dB | lowpass | highpass | reverb |
| ----- | ---- | ----------- | ----------- | ----------- | ------- | -------- | ------ |
| Electronic | 0.9 | 0.6 | 0.4 | 0.2 | 0.9 | 0.8 | 0.7 |
| Folk | 0.8 | 0.5 | 0.5 | 0.4 | 0.8 | 0.8 | 1.0 |
| Instrumental | 0.7 | 0.6 | 0.4 | 0.2 | 0.7 | 0.7 | 0.7 |
| Pop | 0.7 | 0.7 | 0.5 | 0.0 | 0.6 | 0.6 | 0.6 |
| Hip-Hop | 0.6 | 0.3 | 0.3 | 0.2 | 0.6 | 0.6 | 0.7 |
| International | 0.6 | 0.1 | 0.1 | 0.1 | 0.6 | 0.8 | 0.6 |
| Rock | 0.5 | 0.3 | 0.2 | 0.3 | 0.5 | 0.7 | 0.5 |
| Experimental | 0.3 | 0.3 | 0.2 | 0.0 | 0.4 | 0.6 | 0.3 |

## Findings

- **Filtering and reverb do not hurt AudioSeal.** Low-pass 3 kHz, high-pass 300 Hz and reverb
  keep both outputs at the no-attack level (message 0.64-0.70, watermark found 1.00).
- **Gaussian noise damages the message, not the detector.** Even at 30 dB SNR the message is
  read in only 43% of tracks (vs 64% with no attack), dropping to 18% at 10 dB. The detector
  still finds the watermark in 96-100% of tracks. At 30 dB the noise is only about 5 dB
  quieter than the watermark itself (embedding SNR is about 25 dB).
- **The same split as for compression**: "is this track watermarked?" is answered very
  reliably (MP3, AAC, EnCodec >= 12 kbps, gain, crop, filters, reverb, noise), while the 16-bit
  message fails in about a third of tracks even with no attack.
- **Speed and pitch remove the watermark completely**, as for audiowmark. Time stretch is
  partly survived by the message but never by the detector, so it should not be read as
  robustness.
- **No false positives**: on unwatermarked tracks neither output fires (7.7 of 16 bits correct,
  i.e. chance).
- SNR after embedding: mean 25.5 dB (range 19.7-39.3 dB), lower than audiowmark (31.0 dB).

## Limitations
- 80 tracks, 10 per genre: one track is 10 percentage points within a genre, so genre
  differences are preliminary.
- One message, default embedding strength, one parameter setting for each filter and for reverb.
- The 14/16 rule is stricter for AudioSeal than its own detector, so comparing methods on the
  `detected` column alone understates AudioSeal for the yes/no question.
- Gaussian noise uses a fixed seed (42), so every track gets the same noise pattern.
- Tracks 2 and 5 were run on CPU, the rest on GPU (RTX 4060). On track 2 both gave the same
  bits; probabilities differ only in the 4th decimal place.
- No listening tests; the source files were already mp3, converted to WAV.
