#!/bin/sh
rm -rvf ./*.wav ./*.mp4 ./*.m4a ./*.mp3 ./*.opus ./*.ogg ./*.flac
rm -rvf ./build ./dist
rm -rvf ./splits/*
rm -rvf ./tracks.txt ./*_tracks.txt
rm -rvf ./*.webm.part
rm -rfv ./split
rm -rvf ./__pycache__ ./utils/__pycache__ ./MetadataProviders/__pycache__
