# -*- coding: utf-8 -*-
import sys
import re

src = sys.argv[1]
dst = sys.argv[2]

try:
    for enc in ["utf-8", "shift_jis", "cp932", "latin-1"]:
        try:
            with open(src, "r", encoding=enc) as f:
                content = f.read()
            break
        except:
            continue

    content = re.sub(r'\.wav"', '.flac"', content, flags=re.IGNORECASE)
    content = re.sub(r"\.wav'", ".flac'", content, flags=re.IGNORECASE)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK")
except Exception as e:
    print(f"ERR: {e}")
