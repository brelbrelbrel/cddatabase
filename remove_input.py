# -*- coding: utf-8 -*-
# Remove input() from script for background execution
with open('create_music_db.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('input("Press Enter to exit...")', '# input removed for background')

with open('create_music_db.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
