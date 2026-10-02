from datasets import load_dataset, Audio
import os

OUTPUT_DIR = "test_audio"
TARGET = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading call-center dataset...")

dataset = load_dataset(
    "apptek-com/apptek_callcenter_dialogues",
    split="test",
    streaming=True
)

dataset = dataset.cast_column("audio", Audio(decode=False))

count = 0

for row in dataset:

    # Only customer recordings
    if row["role"] != "customer":
        continue

    audio_info = row["audio"]

    # Skip rows without audio
    if audio_info is None:
        continue

    audio_path = audio_info.get("path")

    if not audio_path:
        continue

    filename = os.path.basename(audio_path)
    output_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(output_path):
        continue

    print(f"Downloading {count + 1}/100: {filename}")

    audio_bytes = audio_info.get("bytes")

    if audio_bytes:
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
    else:
        print("Audio bytes unavailable, skipping...")
        continue

    count += 1

    if count >= TARGET:
        break

print()
print(f"DONE! Downloaded {count} customer audio files.")