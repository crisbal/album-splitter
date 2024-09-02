import math
import re
from collections import namedtuple
import eyed3

import typing

Track = namedtuple("Track", ["title", "start_timestamp"])


def parse_time_string(time: str):
    parts = time.strip().split(":")
    seconds = None
    if len(parts) == 3:  # h:m:s
        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:  # m:s
        seconds = int(parts[0]) * 60 + int(parts[1])
    else:
        raise Exception(f"Unknown time format: {time}")
    return seconds


def parse_tracks(tracks_content: str, duration: bool = False) -> typing.List[Track]:
    lines = tracks_content.splitlines()
    tracks: typing.List[Track] = []
    current_time = 0
    for line in lines:
        line = line.strip()
        if line.startswith("#") or len(line) == 0:
            continue
        track_time, title = parse_line(line)
        track_time_seconds = parse_time_string(track_time)
        if not duration:
            current_time = track_time_seconds
        tracks.append(Track(title=title, start_timestamp=current_time))
        if duration:
            current_time += track_time_seconds
    return tracks


def parse_line(line: str) -> typing.Tuple[str, str]:
    line = line.strip()
    # match [HHH:]MM:SS
    timestamp_regex = r"(?:\d+:)?(?:0[0-9]|[1-5][0-9]):(?:0[0-9]|[1-5][0-9])"
    timestamp_regex_beginning = rf"^{timestamp_regex}\b"
    timestamp_regex_end = rf"\b{timestamp_regex}$"
    match_beginning = re.search(timestamp_regex_beginning, line)
    match_end = re.search(timestamp_regex_end, line)
    if match_beginning:
        timestamp = match_beginning.group(0)
        title = re.sub(timestamp_regex_beginning, "", line)
    elif match_end:
        timestamp = match_end.group(0)
        title = re.sub(timestamp_regex_end, "", line)
    else:
        raise ValueError(
            f"Can't find a valid timestamp (HH:MM:SS or MM:SS) at the beginning or at the end of line: {line}"
        )
    title = title.strip(" -|")
    return timestamp, title

def get_tracks_from_tags(audio_file):
    audio = eyed3.load(audio_file)
    chapters = audio.tag.chapters
    tracks = []
    for chapter in chapters:
        title = chapter.title
        times_ms = chapter.times
        start_ms = times_ms[0]
        start_seconds =int(math.floor(start_ms / 1000))
        tracks.append(Track(title=title, start_timestamp=start_seconds))
    return tracks