@echo off
del /Q /F .\*.wav .\*.mp3 .\*.m4a .\*.opus .\*.ogg .\*.flac 2>nul
rmdir /S /Q .\build 2>nul
rmdir /S /Q .\dist 2>nul
rmdir /S /Q .\splits 2>nul
del /Q /F .\tracks.txt .\*_tracks.txt 2>nul
del /Q /F *.webm.part 2>nul
del /Q /F .\split.exe 2>nul
del /Q /F .\__pycache__ .\utils\__pycache__ .\MetadataProviders\__pycache__ 2>nul

