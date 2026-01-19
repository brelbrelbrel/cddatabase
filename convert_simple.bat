@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set "SRC=C:\Users\kawamura\Desktop\wavcue"
set "DST=C:\Users\kawamura\Desktop\flaccue"
set "FFMPEG=C:\ffmpeg.exe"
set "CUEPY=C:\Users\kawamura\Desktop\convert_cue.py"

echo ============================================================
echo WAV to FLAC Converter
echo ============================================================
echo Source: %SRC%
echo Dest:   %DST%
echo.

:: Count files
set total=0
for /r "%SRC%" %%F in (*.wav) do set /a total+=1
echo Total WAV files: %total%
echo.

:: Convert
set count=0
set converted=0
set skipped=0

for /r "%SRC%" %%F in (*.wav) do (
    set /a count+=1
    set "srcfile=%%F"
    set "relpath=!srcfile:%SRC%=!"
    set "dstfile=%DST%!relpath:.wav=.flac!"
    set "srccue=%%~dpnF.cue"
    set "dstcue=%DST%!relpath:.wav=.cue!"

    for %%P in ("!dstfile!") do set "dstdir=%%~dpP"
    if not exist "!dstdir!" mkdir "!dstdir!"

    :: CUE conversion first
    if exist "!srccue!" (
        if not exist "!dstcue!" (
            python "%CUEPY%" "!srccue!" "!dstcue!"
            echo [!count!/%total%] CUE: %%~nF.cue
        )
    )

    if exist "!dstfile!" (
        set /a skipped+=1
        echo [!count!/%total%] SKIP: %%~nxF
    ) else (
        echo [!count!/%total%] CONVERTING: %%~nxF
        "%FFMPEG%" -i "%%F" -c:a flac -compression_level 8 "!dstfile!" -y -loglevel warning
        if exist "!dstfile!" (
            set /a converted+=1
            echo             DONE
        ) else (
            echo             ERROR
        )
    )
)

echo.
echo ============================================================
echo COMPLETE: Converted=%converted% Skipped=%skipped%
echo ============================================================
pause
