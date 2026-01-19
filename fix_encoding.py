# -*- coding: utf-8 -*-
import sys

# Read original
with open('create_music_db.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add encoding fix after imports
fix = '''import sys
import io
# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
'''

if 'io.TextIOWrapper' not in content:
    content = content.replace('import os\n', 'import os\n' + fix, 1)
    with open('create_music_db.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed!')
else:
    print('Already fixed')
