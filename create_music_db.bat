@echo off
chcp 65001 > nul
cd /d C:\Users\kawamura\Desktop
set PYTHONIOENCODING=utf-8
python create_music_db.py
pause
