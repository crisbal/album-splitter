import subprocess
from pathlib import Path
from typing import Dict, List

import ffmpy

from .parse_tracks import Track


def split_file(
    input_file: Path, tracks: List[Track], destination: Path, output_format: str
):
    duration_command = ffmpy.FFprobe(
        inputs={str(input_file): '-show_entries format=duration -v quiet -of csv="p=0"'}
    )
    stdout, _ = duration_command.run(stdout=subprocess.PIPE)
    file_duration = float(stdout.decode().strip())
    outputs: Dict[Path, str] = {}

    max_zero_padding = len(str(len(tracks)))
    for i, track in enumerate(tracks):
        start_timestamp = track.start_timestamp
        end_timestamp = (
            file_duration if i == len(tracks) - 1 else tracks[i + 1].start_timestamp
        )
        outputs[
            destination
            / (f"{str(i+1).zfill(max_zero_padding)} {track.title}.{output_format}")
        ] = f"-vn -c copy -ss {start_timestamp} -to {end_timestamp}"
    split_command = ffmpy.FFmpeg(
        inputs={str(input_file): "-y -hide_banner -loglevel error -stats"},
        outputs={str(path): v for path, v in outputs.items()},
    )
    try:
        split_command.run()
    except:
        raise Exception(
            "Something went wrong with the splitting procedure. See the error above."
        ) from None

    return list(outputs.keys())
