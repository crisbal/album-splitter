# tracks_parser.py
# The parsing part!

import io

from .track_parser import track_parser
from .time_to_seconds import time_to_seconds
from .update_time_change import update_time_change


def tracks_parser(tracks_info_file, DRYRUN, DURATION):
    tracks_start = []
    tracks_titles = []
    with io.open(tracks_info_file, 'r', encoding='utf8') as tracks_file:
        time_elapsed = '0:00:00'
        for i, line in enumerate(tracks_file):
            stripped_line = line.strip()
            if len(stripped_line) > 0 and stripped_line[0] != '#':
                curr_start, curr_title = track_parser(line)

                if DRYRUN:
                    print(curr_title + " *** " + curr_start)

                if DURATION:
                    t_start = time_to_seconds(time_elapsed)
                    time_elapsed = update_time_change(time_elapsed, curr_start)
                else:
                    t_start = time_to_seconds(curr_start)

                tracks_start.append(t_start * 1000)
                tracks_titles.append(curr_title)

    return tracks_start, tracks_titles

def tracks_parser_embed(tracks_info_text, DURATION):
    tracks_start = []
    tracks_titles = []
    time_elapsed = '0:00:00'
    
    tracks_info_list = tracks_info_text.split('\n')
    for i, line in enumerate(tracks_info_list):
        stripped_line = line.strip()
        if len(stripped_line) > 0 and stripped_line[0] != '#':
            curr_start, curr_title = track_parser(line)

            if curr_start == '' and curr_title == '':
                continue

            if DURATION:
                t_start = time_to_seconds(time_elapsed)
                time_elapsed = update_time_change(time_elapsed, curr_start)
            else:
                t_start = time_to_seconds(curr_start)

            tracks_start.append(t_start * 1000)
            tracks_titles.append(curr_title)

    return tracks_start, tracks_titles
