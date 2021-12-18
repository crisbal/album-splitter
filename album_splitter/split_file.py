from pathlib import Path
import subprocess
from .parse_tracks import Track

import ffmpy

from typing import List, Dict

def split_file(input_file: Path, tracks: List[Track], destination: Path, output_format: str):
    duration_command = ffmpy.FFprobe(
        inputs={str(input_file): '-show_entries format=duration -v quiet -of csv="p=0"'}
    )
    stdout, _ = duration_command.run(stdout=subprocess.PIPE)
    file_duration = float(stdout.decode().strip())
    outputs: List[str] = []
    for i, track in enumerate(tracks):
        start_timestamp = track.start_timestamp
        end_timestamp = file_duration if i == len(tracks) - 1 else tracks[i + 1].start_timestamp
        output_file = destination / (f"{track.title}.{output_format}")
        outputs.append(output_file)
            
        split_command = ffmpy.FFmpeg(
            inputs={str(input_file): f"-y -hide_banner -loglevel error -stats -ss {start_timestamp} -t {end_timestamp}"},
            outputs={ str(output_file): "-c copy" }
        )
        try:
            split_command.run()
        except:
            raise Exception("Something went wrong with the splitting procedure. See the error above.") from None

    return outputs
