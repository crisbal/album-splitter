#!/usr/bin/env python3

import argparse
import os
import sys
import re
from queue import Queue
from threading import Thread
from urllib.parse import urlparse, parse_qs
import subprocess as sbp
# from uuid import uuid4

from pydub import exceptions as pydub_excpetions
from pydub import AudioSegment
from youtube_dl import YoutubeDL

from split_init import METADATA_PROVIDERS, ydl_opts
from utils import (split_song, time_to_seconds,
                   track_parser, update_time_change,
                   tracks_editor)

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

PYDUB_MAX_SIZE = 4*1024*1024


def thread_func(album, tracks_start, queue, FOLDER, ARTIST, ALBUM, FILE_TYPE, TRK_TIMESKIP, FFMPEG_MODE):
    while not queue.empty():
        song_tuple = queue.get()
        split_song(album, tracks_start, song_tuple[0], song_tuple[1],
                   FOLDER, ARTIST, ALBUM, BITRATE, FILE_TYPE, TRK_TIMESKIP_F, TRK_TIMESKIP_R, FFMPEG_MODE)


if __name__ == "__main__":
    # arg parsing
    parser = argparse.ArgumentParser(
        description='Split a single-file Album into its tracks.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-mp3", help="The .mp3 file you want to split.", metavar="mp3_file")
    group.add_argument(
        "-m4a", help="The .m4a file you want to split.", metavar="m4a_file")
    group.add_argument(
        "-yt", help="The YouTube video url you want to download and split.", metavar="youtube_url"
    )
    parser.add_argument(
        "-a", "--artist",
        help="Specify the artist that the mp3s will be ID3-tagged with. Default: no tag",
        default=None
    )
    parser.add_argument(
        "-A", "--album",
        help="Specify the album that the mp3s will be ID3-tagged with. Default: no tag",
        default=None
    )
    parser.add_argument(
        "-t", "--tracks", help="Specify the tracks file. Default: tracks.txt", default="tracks.txt"
    )
    parser.add_argument(
        "-f", "--folder",
        help="Specify the folder the mp3s will be put in. Default: splits/",
        default=None
    )
    parser.add_argument(
        "-d", "--duration",
        dest='duration',
        action='store_true',
        help="Specify track time format will use the duration of each individual song. "
             "Default: False",
        default=False
    )
    parser.add_argument(
        "-th", "--threaded",
        dest='threaded',
        action='store_true',
        help="Specify the script should use threads. Default: False",
        default=False
    )
    parser.add_argument(
        "--num-threads",
        dest='num_threads',
        help="Specify the (whole/non-negative) number of threads the script should spawn when "
             "using threads. Default: 3",
        default='3'
    )
    parser.add_argument(
        "--metadata",
        dest='metadata',
        help="Specify the source for the Album Metadata.",
        default="file"
    )
    parser.add_argument(
        "--dry-run",
        dest='dry',
        action='store_true',
        help="Don't split the file, just output the tracks, useful for seeing if the tracks.txt "
             "format is ok or needs tweaking.",
        default=False
    )
    parser.add_argument(
        "-bitrate",
        help="Specify the bitrate of the export. Default: '320k'",
        default="320k"
    )
    parser.add_argument(
        "-of", "--output-format",
        help="Specify the output file format. Dependent on FFMpeg. Default: m4a",
        dest="output_format",
        default="m4a"
    )
    parser.add_argument(
        "-ttsf", "--track-timeskip-front",
        help="Specify timeskip from start in each track in ms. Default: 0 ms",
        dest="trk_timeskip_f",
        default=0
    )
    parser.add_argument(
        "-ttsr", "--track-timeskip-rear",
        help="Specify timeskip from the end in each track in ms. Default: 0 ms",
        dest="trk_timeskip_r",
        default=0
    )
    args = parser.parse_args()
    FILE_TYPE = args.output_format.lower()
    if args.mp3:
        FILENAME = args.mp3
        FILE_TYPE = "mp3"
    elif args.m4a:
        FILENAME = args.m4a
        FILE_TYPE = "m4a"
    YT_URL = args.yt
    ALBUM = args.album
    ARTIST = args.artist
    DURATION = args.duration
    THREADED = args.threaded
    NUM_THREADS = int(args.num_threads)
    METASRC = args.metadata
    DRYRUN = args.dry
    BITRATE = args.bitrate
    TRK_TIMESKIP_F = int(args.trk_timeskip_f)
    TRK_TIMESKIP_R = int(args.trk_timeskip_r)
    TRACKS_FILE_NAME = args.tracks
    FFMPEG_MODE = False

    if DRYRUN:
        print("**** DRY RUN ****")

    if args.folder is None:
        if ALBUM and ARTIST:
            FOLDER = "{} - {}".format(ARTIST, ALBUM)
        else:
            if YT_URL:
                url_data = urlparse(YT_URL)
                query = parse_qs(url_data.query)
                video_id = query["v"][0]
                FOLDER = "./splits/{}".format(video_id)
                TRACKS_FILE_NAME = "{}_{}".format(video_id, 'tracks.txt')
            else:
                # FOLDER = "./splits/{}".format(str(uuid4())[:16])
                FOLDER = "./splits/{}".format(os.path.basename(FILENAME))
    else:
        FOLDER = args.folder

    # create destination folder
    if not os.path.exists(FOLDER) and not DRYRUN:
        os.makedirs(FOLDER)

    if METASRC != "file":
        found_a_source = False
        for provider in METADATA_PROVIDERS:
            pattern = re.compile(provider.VALID_URL)
            if pattern.match(METASRC):
                print("Matched with a metadata provider...")
                if not provider.lookup(METASRC, TRACKS_FILE_NAME):
                    print(
                        "Can't find a track list in the provided source. Shutting Down.")
                    exit()
                else:
                    found_a_source = True
                    break
        if not found_a_source:
            print("There was no provider able to get data from your source!")
            exit()

    tracks_start = []
    tracks_titles = []

    # Let's check up if tracks file exists!!
    # if not, open an editor window
    if not os.path.isfile(TRACKS_FILE_NAME):
        app = QApplication(sys.argv)
        app.setApplicationName("split.py - Tracks Editor")
        te = tracks_editor(trk_fname=TRACKS_FILE_NAME)
        app.exec_()
        te.close()

    print("Parsing " + TRACKS_FILE_NAME)
    with open(TRACKS_FILE_NAME) as tracks_file:
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

    if DRYRUN:
        exit()

    print("Tracks file parsed")
    print("# of tracks found: {}".format(len(tracks_start)))
    print()

    album = None
    if YT_URL:
        url_data = urlparse(YT_URL)
        query = parse_qs(url_data.query)
        video_id = query["v"][0]
        FILENAME = "{}.{}".format(video_id, FILE_TYPE)
        if not os.path.isfile(FILENAME):
            print("Downloading video from YouTube")
            # convert the source file into the desired output format.
            ydl_opts['postprocessors'] = \
                [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': FILE_TYPE.lower(),
                    'preferredquality': '0',
                }]
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(['http://www.youtube.com/watch?v=' + video_id])
            print("\nConversion complete")
        else:
            print("Found matching file")
        print("Loading audio file")

        if os.stat(FILENAME).st_size < PYDUB_MAX_SIZE:
            album = AudioSegment.from_file(FILENAME, 'wav')
        else:
            album = FILENAME
            FFMPEG_MODE = True

    else:
        print("Loading audio file")
        file_ext = os.path.splitext(FILENAME)[-1].replace('.', '').lower()
        f_size =  os.stat(FILENAME).st_size
        if file_ext != 'wav':
            f_size *= 5

        if f_size < PYDUB_MAX_SIZE:
            album = AudioSegment.from_file(FILENAME, file_ext)
        else:
            album = FILENAME
            FFMPEG_MODE = True

    print("Audio file loaded")
    if FFMPEG_MODE:
        print("Too large file! FFMpeg will be used!")

    if FFMPEG_MODE:
        # Let's convert the album file into corresponding format.
        album_ext = os.path.splitext(album)[-1].replace('.', '').lower()
        if album_ext != FILE_TYPE:
            cmd_convert = 'ffmpeg -i "{inf}" -ab {br} -y "{nm}.{fmt}"'
            file_basename = os.path.splitext(os.path.realpath(album))[0]
            print("Converting the album file to designated output file.")
            cmd = cmd_convert.format(
                inf=os.path.realpath(album), br=BITRATE, nm=file_basename, fmt=FILE_TYPE)
            sbp.call(cmd, shell=True)
            # print("Removing the source file... to save space.")
            # os.remove(album)
            album = "{}.{}".format(file_basename, FILE_TYPE)

        if FILE_TYPE == 'mp3':
            tracks_start.append(MP3(album).info.length * 1000)
        elif FILE_TYPE == 'mp4' or FILE_TYPE == 'm4a':
            tracks_start.append(MP4(album).info.length * 1000)
        else:
            print("Uh oh... not sure how to handle other files w/o pydub")
    else:
        # we need this for the last track/split
        tracks_start.append(len(album))

    print("Starting to split")
    if THREADED and NUM_THREADS > 1:
        # Create our queue of indexes and track titles
        queue = Queue()
        for index, track in enumerate(tracks_titles):
            queue.put((index, track))
        # initialize/start threads
        threads = []
        for i in range(NUM_THREADS):
            new_thread = Thread(target=thread_func, args=(
                album, tracks_start, queue, FOLDER, ARTIST, ALBUM, FILE_TYPE, TRK_TIMESKIP_F, TRK_TIMESKIP_R, FFMPEG_MODE))
            new_thread.start()
            threads.append(new_thread)
        # wait for them to finish
        for thread in threads:
            thread.join()
    # Non threaded execution
    else:
        tracks_titles.append("END")
        for i, track in enumerate(tracks_titles):
            if i != len(tracks_titles) - 1:
                split_song(album, tracks_start, i, track, FOLDER,
                           ARTIST, ALBUM, BITRATE, FILE_TYPE, TRK_TIMESKIP_F, TRK_TIMESKIP_R, FFMPEG_MODE)
    print("All Done")
