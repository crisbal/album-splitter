@echo off
rem pip install -U pyinstaller
set PYTHONOPTIMIZE=1 && pyinstaller .\split.spec
copy /Y .\dist\split.exe .\

if %1 == "build" GOTO DONE
copy /Y .\split.exe "C:\FFMpeg\bin"

:DONE