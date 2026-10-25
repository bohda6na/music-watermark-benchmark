# Classical watermarking methods and the choice of the third method

Purpose: a short review of classical (non-neural) audio watermarking, and the reasons why
the benchmark uses audiowmark next to the two neural methods (AudioSeal, WavMark).

## Overview

| Method | Idea | Detection | Typical strengths | Typical weaknesses |
|---|---|---|---|---|
| LSB coding | Replace the least significant bits of samples with message bits | read the bits | trivial, high capacity | destroyed by any lossy operation (mp3, resampling, noise) |
| Phase coding | Encode bits in the phase of short-time spectrum segments, keeping relative phase between segments | compare phases | the ear is relatively insensitive to phase | low capacity, sensitive to compression and resampling |
| Echo hiding | Add a very quiet echo; its delay encodes the bit (one delay for 0, another for 1) | cepstrum / autocorrelation | inaudible for short delays, simple | strong reverberation and filtering interfere with the echo |
| Spread spectrum | Add a keyed pseudo-random noise sequence modulated by the message, at low energy over a wide band | correlation with the same sequence | blind detection, robust to noise and compression when the sequence is long | the host music acts as interference; breaks when the signal is shifted or time-scaled and not re-synchronised |
| Patchwork | Choose two keyed pseudo-random sets of time or spectral elements and shift one set slightly up and the other down | statistic of the difference between the sets | blind detection, statistical (robust to small noise) | needs synchronisation, low capacity |

The descriptions follow the classical papers: Bender et al., "Techniques for data hiding"
(IBM Systems Journal, 1996) for LSB, phase coding, spread spectrum, echo hiding and
patchwork; Gruhl et al., "Echo hiding" (1996); Cox et al., "Secure spread spectrum
watermarking for multimedia" (IEEE Trans. Image Processing, 1997). The strengths and
weaknesses are the commonly reported ones, not our own measurements.

Common weak point of all classical methods: desynchronisation. Time stretching, speed change
and pitch shift move the positions the detector looks at, so detection fails unless the
method has a re-synchronisation step. This is the main reason to include time and
dynamics attacks in the benchmark.

## Selection criteria for the third method

1. Open source and runnable from a command line, so that anyone can reproduce the runs.
2. Blind detection (the original track is not needed), as for AudioSeal and WavMark.
3. A message of our own fixed length can be embedded (16 bits).
4. Designed for realistic conditions (lossy compression), not only for a lab.
5. Different family from the other two methods (not neural), so that the benchmark can
   compare classical and neural approaches.
6. Runs on Linux / Google Colab without special hardware.

## Chosen method: audiowmark

audiowmark (Stefan Westerfeld, https://github.com/swesterfeld/audiowmark) meets all six
criteria:

- It is an open-source C++ tool with `add` and `get` commands, and it embeds a 128-bit
  message by default; the `--short` mode lets us use 16 bits.
- Detection is blind, and it uses forward error correction; the documentation states that the
  watermark can survive lossy formats such as MP3 and OGG.
- Internally it uses the patchwork algorithm in the audio spectrum (so, strictly, it is a
  frequency-domain patchwork method, a close relative of spread spectrum).
- It has an optional speed detection mode (`--detect-speed`), which is the only
  re-synchronisation feature among our methods. We keep it off in the main comparison
  because AudioSeal and WavMark have no equivalent, and report it as a separate experiment.
- License: GPL-3.0 or later. We call it as an external program and do not include its code.

Alternatives considered: writing our own echo hiding or phase coding implementation. We did
not do it, because the benchmark would then measure the quality of our implementation
instead of an established method, and the time before the midterm is limited.

## What we found

On 80 tracks audiowmark survives gain, crop, MP3/AAC, low-pass, high-pass and reverb (1.00)
and Gaussian noise at 30 dB (1.00) and 20 dB (0.98); at 10 dB it loses 16 of 80 tracks (0.80).
It fails on speed, time stretch and pitch shift (0.00), as expected from desynchronisation,
and on the EnCodec neural codec at every bitrate (0.00). With `--detect-speed` it reads the
message at speed 0.9x and 1.1x in all 80 tracks. Details: `results/README.md`.

## Sources

- audiowmark repository and releases: https://github.com/swesterfeld/audiowmark
- audiowmark manual page (Debian): https://dyn.manpages.debian.org/testing/audiowmark/audiowmark.1
- audiowmark in FreeBSD ports (describes the patchwork algorithm): https://freshports.org/audio/audiowmark
- W. Bender, D. Gruhl, N. Morimoto, A. Lu, "Techniques for data hiding", IBM Systems Journal 35(3.4), 1996.
- D. Gruhl, A. Lu, W. Bender, "Echo hiding", Information Hiding workshop, 1996.
- I. Cox, J. Kilian, T. Leighton, T. Shamoon, "Secure spread spectrum watermarking for multimedia", IEEE Trans. Image Processing 6(12), 1997.
