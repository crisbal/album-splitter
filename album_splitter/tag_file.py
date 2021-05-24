import music_tag
from pathlib import Path


def tag_file(file: Path, tag_data: dict[str, str]):
    audio = music_tag.load_file(file)
    for tag, data in tag_data.items():
        if data:
            audio[tag] = data
    audio.save()
