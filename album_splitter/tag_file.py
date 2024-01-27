from pathlib import Path
from typing import Dict

import music_tag


def tag_file(file: Path, tag_data: Dict[str, str]):
    audio = music_tag.load_file(file)
    if not audio:
        raise RuntimeError(
            f"Something went wrong when loading file for tagging: {file}"
        )

    for tag, data in tag_data.items():
        if tag in ["artwork"] and isinstance(data, str):
            if Path(data).exists():
                with open(data, "rb") as img_in:
                    data = img_in.read()
            else:
                print(f"Warning: no artwork file found at {data}, skipping.")
                continue

        if data:
            audio[tag] = data

    audio.save()
