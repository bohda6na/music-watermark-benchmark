
import librosa
import numpy as np
import wavmark

# 1. Завантажуємо готову модель
print("1. Loading model...", flush=True)
model = wavmark.load_model()
print("2. Model loaded!", flush=True)

# 2. Завантажуємо музичний трек
audio, sr = librosa.load(
    "fma_small/000/000002.mp3",
    sr=16000,
    mono=True
)

# 3. Створюємо 16-бітний watermark
message = np.array([int(b) for b in "1010010111000011"])

# 4. Вбудовуємо watermark
print("3. Encoding watermark...", flush=True)

watermarked, _ = wavmark.encode_watermark(
    model, audio, message, show_progress=False
)

print("4. Encoding finished!", flush=True)

# 5. Відновлюємо повідомлення
print("5. Decoding watermark...", flush=True)

decoded, _ = wavmark.decode_watermark(
    model, watermarked, show_progress=False
)

print("6. Decoding finished!", flush=True)
print("Original:", message)
print("Decoded:", decoded)

if decoded is not None:
    accuracy = np.mean(message == decoded)
    print("Bit accuracy:", accuracy)
