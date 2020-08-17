@echo off
rem pip install -U pyinstaller
pyinstaller .\split.spec
copy /Y .\dist\split.exe .\

if %1 == "buil" GOTO DONE
copy /Y .\split.exe "C:\FFMpeg\bin"

:DONE