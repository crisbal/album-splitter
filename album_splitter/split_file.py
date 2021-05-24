from pathlib import Path
import subprocess
from .parse_tracks import Track

import ffmpy


def split_file(input_file: Path, tracks: list[Track], destination: Path, output_format: str):
    duration_command = ffmpy.FFprobe(
        inputs={input_file: '-show_entries format=duration -v quiet -of csv="p=0"'}
    )
    stdout, _ = duration_command.run(stdout=subprocess.PIPE)
    file_duration = float(stdout.decode().strip())
    outputs: dict[Path, str] = {}
    for i, track in enumerate(tracks):
        start_timestamp = track.start_timestamp
        end_timestamp = file_duration if i == len(tracks) - 1 else tracks[i + 1].start_timestamp
        outputs[
            destination / (f"{track.title}.{output_format}")
        ] = f"-ss {start_timestamp} -to {end_timestamp}"
    split_command = ffmpy.FFmpeg(
        inputs={input_file: "-y -hide_banner -loglevel error -stats"}, outputs=outputs
    )
    try:
        split_command.run()
    except:
        raise Exception("Something went wrong with the splitting procedure. See the error above.") from None

    return list(outputs.keys())
