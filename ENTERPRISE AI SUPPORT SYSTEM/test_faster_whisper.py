from faster_whisper import WhisperModel
import time

audio_file = r"test_audio\en_IN_Banking_003_20250917_channel2.wav"

print("Loading faster-whisper model...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("Model loaded. Starting transcription...")

start = time.time()

segments, info = model.transcribe(
    audio_file,
    beam_size=1
)

transcript = " ".join(segment.text for segment in segments)

elapsed = time.time() - start

print("\n==============================")
print("TRANSCRIPTION TIME:", round(elapsed, 2), "seconds")
print("==============================")
print("\nTRANSCRIPT:")
print(transcript)