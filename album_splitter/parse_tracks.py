import re
from collections import namedtuple

import typing

from .utils.secure_filename import secure_filename_simple

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
        tracks.append(Track(title=secure_filename_simple(title), start_timestamp=current_time))
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


timestamp_regex = re.compile(r"((?:\d+:)?[0-5]?\d:[0-5]?\d)")
timestamp_regex_text = re.compile(r"^(.*?)((?:\d+:)?[0-5]?\d:[0-5]?\d)(.*)$")

trailing_chars_regex = re.compile(r"^[\s|:\-_~)\]., }>]+")
leading_chars_regex = re.compile(r"[\s|:_(\[{<., ]+$")

def infer_tracks_from_text(text: str) -> typing.List[Track]:
    """
    Try to infer a tracklist from a non-formatted text.
    It assumes the timestamps are in [hh]:mm:ss format and come always in the same order.
    The track name is everything between timestamps, cleaned up.

    :param text: The text to parse.

    :return: A list of tracks.
    """

    # find the first line that contains a timestamp (left, timestamp, right)
    lines: typing.List[typing.Union[str, typing.List[str]]] = text.splitlines()
    timestamps = [timestamp_regex.findall(line) for line in lines]

    # if a line contains more than 3 timestamps, it's probably a list of timestamps + track name
    # so we cut, looking at which side the timestamps are
    for i in range(len(timestamps)):
        if 3 < len(timestamps[i]):
            timestamps = timestamps[i]
            line = lines[i]
            timestamps_positions = [line.find(timestamp) for timestamp in timestamps]

            # check which side the timestamps are, the side with the least chars is the track name
            first_timestamp = timestamps_positions[0]
            last_timestamp = timestamps_positions[-1]
            side = len(line[:first_timestamp].strip()) < len(line[last_timestamp + len(timestamps[-1]):].strip())

            # cut the line (side == 0 is left, side == 1 is right)
            if side:
                timestamps_positions.append(len(line))
                timestamp_lines = [line[a:b] for a, b in zip(timestamps_positions, timestamps_positions[1:])]
            else:
                timestamps_positions.insert(0, 0)
                timestamp_lines = [line[a:b] for a, b in zip(timestamps_positions, timestamps_positions[1:])]

            lines[i] = timestamp_lines
        else:
            lines[i] = [lines[i]]

    # flatten the list
    lines = [line for sublist in lines for line in sublist]

    timestamp_lines = [timestamp_regex_text.search(line) for line in lines]
    timestamp_lines = [line.groups() for line in timestamp_lines if line is not None]

    # choose the right side to get the track name
    tracks_infos = [
        (right if len(left) < len(right) else left, timestamp) for left, timestamp, right in timestamp_lines
    ]

    # clean up the track name (remove additional timestamps, trailing and leading chars)
    tracks_infos = [
        (trailing_chars_regex.sub("", leading_chars_regex.sub("", timestamp_regex.sub("", track_name))), timestamp)
        for track_name, timestamp in tracks_infos
    ]

    # TODO: throw an error if name is empty ?

    # create tracks
    tracks = [
        Track(title=secure_filename_simple(track_name), start_timestamp=parse_time_string(timestamp))
        for track_name, timestamp in tracks_infos
    ]

    return tracks
