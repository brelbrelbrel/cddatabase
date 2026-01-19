
import os
import subprocess
from pathlib import Path

WAV_DIR = r"C:\Users\kawamura\Desktop\wavcue"
FLAC_DIR = r"C:\Users\kawamura\Desktop\flaccue"

def get_rel_path(path, start):
    return os.path.relpath(path, start)

print("Scanning for missing FLAC files...")
missing_files = []

for root, _, filenames in os.walk(WAV_DIR):
    for name in filenames:
        if name.lower().endswith(".wav"):
            wav_path = os.path.join(root, name)
            rel_path = get_rel_path(wav_path, WAV_DIR)
            
            # Construct expected FLAC path
            flac_rel = os.path.splitext(rel_path)[0] + ".flac"
            flac_path = os.path.join(FLAC_DIR, flac_rel)
            
            if not os.path.exists(flac_path):
                missing_files.append((wav_path, flac_path))

print(f"Found {len(missing_files)} missing FLAC files.")

for i, (wav, flac) in enumerate(missing_files, 1):
    print(f"[{i}/{len(missing_files)}] Converting: {os.path.basename(wav)}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(flac), exist_ok=True)
    
    # Run ffmpeg
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', wav, 
            '-compression_level', '5', 
            '-v', 'error', 
            flac
        ], check=True)
        print(f"  -> Saved to {flac}")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error converting {wav}: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")

print("\nConversion complete!")
