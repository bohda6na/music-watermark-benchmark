# Metrics and thresholds

## Embedding quality: SNR
SNR (dB) = 10 * log10( sum(x^2) / sum((y - x)^2) )
where x is the original signal and y is the watermarked signal.
Higher SNR means the watermark changed the signal less.

## Detection criterion
A track is counted as *detected* when:
| Method | Criterion | Threshold |
|---|---|---|
| audiowmark | bit accuracy over the 16-bit message | >= 14/16 (0.875) |
| AudioSeal | (поріг, який ви домовитесь) | ... |
| WavMark | bit accuracy over the 16-bit message | ... |

## Why these thresholds
(2–3 речення: чому 14/16 для audiowmark; що буде, якщо повідомлення випадкове)

## Primary metric
Detection rate = share of the 80 tracks with detected = True,
per (method, attack, params, genre).

## Message
16-bit message, the same for all methods.