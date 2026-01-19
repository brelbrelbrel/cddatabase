
import os
from pathlib import Path

WAV_DIR = r"C:\Users\kawamura\Desktop\wavcue"
FLAC_DIR = r"C:\Users\kawamura\Desktop\flaccue"

def get_files(directory, ext):
    files = set()
    for root, _, filenames in os.walk(directory):
        for name in filenames:
            if name.lower().endswith(ext):
                rel_dir = os.path.relpath(root, directory)
                rel_file = os.path.join(rel_dir, name).replace(".wav", "").replace(".flac", "")
                files.add(rel_file)
    return files

print("Scanning directories...")
wav_files = get_files(WAV_DIR, ".wav")
flac_files = get_files(FLAC_DIR, ".flac")

print(f"Total WAV files: {len(wav_files)}")
print(f"Total FLAC files: {len(flac_files)}")

missing_in_flac = wav_files - flac_files
extra_in_flac = flac_files - wav_files

if missing_in_flac:
    print(f"\n❌ Missing in FLAC ({len(missing_in_flac)} files):")
    for f in sorted(list(missing_in_flac))[:20]:
        print(f"  - {f}")
    if len(missing_in_flac) > 20:
        print(f"  ...and {len(missing_in_flac)-20} more")
else:
    print("\n✅ All WAV files have corresponding FLAC files.")

if extra_in_flac:
    print(f"\nℹ️ Extra files in FLAC ({len(extra_in_flac)} files):")
    # Optional: show a few
    for f in sorted(list(extra_in_flac))[:5]:
        print(f"  - {f}")

# Check for entire missing folders
wav_folders = set(os.listdir(WAV_DIR))
flac_folders = set(os.listdir(FLAC_DIR))
missing_folders = wav_folders - flac_folders
if missing_folders:
    print(f"\n❌ Missing Genres/Folders in FLAC: {missing_folders}")
