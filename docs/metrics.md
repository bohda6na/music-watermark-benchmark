# Metrics and thresholds

## Embedding quality: SNR

SNR (dB) = 10 * log10( sum(x^2) / sum((y - x)^2) )

where x is the original signal and y is the watermarked signal (same length, mono, 44.1 kHz).
Higher SNR means the watermark changed the signal less. SNR is always computed between the
original and the watermarked track, **before** any attack, so it describes the cost of the
method and does not depend on the attack. SNR does not measure how audible the change is; we
ran no listening tests.

## Detection criterion

All methods embed the same 16-bit message. A track counts as **detected** when the decoder
returns a message and its bit accuracy is at least 14/16 (0.875), that is, at most 2 wrong bits.

| Method | Decoder output | detected = True when |
|---|---|---|
| audiowmark | 16 bits, or nothing if no pattern is found | bit accuracy >= 14/16; no output counts as not detected |
| AudioSeal | probability that the audio is watermarked + 16 bits | bit accuracy >= 14/16 (the probability is saved as `detect_prob`, but it is not used for the decision) |
| WavMark | 16 bits, or nothing if no pattern is found | bit accuracy >= 14/16; no output counts as not detected (to be confirmed with the WavMark owner) |

## Why 14/16

If there is no watermark, the decoded bits are close to random. The chance that at least
14 of 16 random bits are correct is (C(16,14) + C(16,15) + C(16,16)) / 2^16 = (120 + 16 + 1) / 65536,
about 0.21%. So one false detection is expected in about 480 unmarked tracks. The threshold is
strict enough to keep false positives rare, and still allows 2 wrong bits, so the result is
not decided by a single flipped bit. We check false positives directly with the
`unwatermarked` control rows (detection on the original track), which must give a detection
rate near 0.

## Primary metric

Detection rate = share of tracks with `detected = True`, per (method, attack, params, genre).
For all genres together n = 80, per genre n = 10, so per-genre rates change in steps of 0.1.
Report the counts (for example 7/10) next to the rates, and treat differences of one or two
tracks between genres as noise. For per-genre comparisons use a confidence interval
(Wilson interval for a proportion).

Secondary metrics: mean bit accuracy over the tracks where a message was decoded, and SNR
per genre (no attack).

## Message and files

- The message is one fixed 16-bit string for all methods (`MESSAGE` in `scripts/common.py`).
- Result files are CSV with the columns
  `method, attack, params, genre, track_id, detected, snr, bit_acc` (the scripts also
  write `detect_prob`; it is empty for methods without a probability output).
- `detected` is written as 1/0. `bit_acc` is empty when the decoder returned no message.
- `attack = unwatermarked` rows are the false-positive control, `attack = none` rows are the
  baseline without an attack.