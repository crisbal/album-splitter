from collections import namedtuple
import re

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


def parse_tracks(tracks_content: str, duration: bool = False):
    lines = tracks_content.splitlines()
    tracks: list[Track] = []
    current_time = 0
    for line in lines:
        if line.startswith("#"):
            continue
        else:
            track_time, title = parse_line(line)
            track_time_seconds = parse_time_string(track_time)
            if not duration:
                current_time = track_time_seconds
            tracks.append(Track(title=title, start_timestamp=current_time))
            if duration:
                current_time += track_time_seconds
    return tracks


def parse_line(line: str):
    """
    Matches any combination of the following:
    Beginning of a line:
        - 1. to 99.
        - 1 to 99
        - title
        - time in HH(optional):MM(required):SS(required) format
    Middle:
        - dash between spaces (' - ') separating the title and the time
    End of the line:
        - title
        - time in HH(optional):MM(required):SS(required) format

    Achieves the split by assuming as noise, every regex in the NOISE list.
    """
    NOISE = [" - ", "^-", "(?:-)?[0-9]{1,2} - ", "(?:-)?[0-9]{1,2}\."]
    # a few years have passed and this reads like magic
    try:
        # Explanation:                     HH optional          MM   and   SS required
        regex = re.compile("(?P<start>(?:([01]?\d|2[0-3]):)?([0-5]?\d):([0-5]?\d))")
        start_time = regex.search(line).group("start")
        title = re.sub("|".join(NOISE), "", regex.sub("", line, count=1)).strip()
        return start_time, title
    except AttributeError:
        raise Exception(f"Error occurred when parsing the line: {line}")
