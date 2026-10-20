# Data card

## Source
FMA (Free Music Archive), subset **fma_small**: 8,000 tracks of 30 s, 8 balanced
genres (1,000 tracks per genre). Source: https://github.com/mdeff/fma

We download two archives:
- `fma_metadata.zip` (342 MB): `tracks.csv` with genres and track ids;
- `fma_small.zip` (7.2 GB): the audio files (mp3).

After downloading, the SHA-1 of `fma_small.zip` is checked against the value from the
FMA documentation (`ade154f733639d52e35e32f5593efe5be76c6d70`).

## Test subset used in this project
Tracks from the `small` subset are sorted by `track_id`, and the **first 10 tracks of each
genre** are taken: 8 genres x 10 tracks = **80 tracks**. The rule is deterministic, so every
team member gets the same tracks. The list is saved as `selected_80.csv`
(columns: `track_id`, `genre`).

## Preprocessing
The 80 mp3 files are converted to WAV, **mono, 44.1 kHz**, so that all watermarking methods
get the same input. Note: the original FMA files are already mp3, so our "original" is a
decoded mp3.

## What is NOT in this repository
Audio files are not committed: they are large and each track has its own license. This
folder is gitignored (`data/raw/`). To get the data, run sections 1-3 of
`notebooks/01_audiowmark_baseline.ipynb`.

## License and terms of use
- Metadata: CC BY 4.0.
- Audio: license chosen by each artist (mostly Creative Commons: CC BY, CC BY-NC, CC BY-SA).
  We use the audio only for non-commercial research and education and do not redistribute it.
- audiowmark (https://github.com/swesterfeld/audiowmark) is licensed under GPL. We run it as
  an external program and do not include its code in this repository.

## Personal data
None. The data contain only public track metadata (track id, genre). No personal data is
stored in this repository.

## Scraping
None. The data are downloaded from the official FMA distribution.

## Risks and limitations
- Only 80 tracks (10 per genre) of 30 s each: genre-level conclusions are preliminary.
- Results for 30 s clips may not carry over to full-length tracks or to other genres.
- A watermark detector is a tool for provenance checks. A "not detected" result does not prove
  that a track was never watermarked.