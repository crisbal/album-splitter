#!/usr/bin/env python3
import argparse
import os
import sys
import re
import io
from queue import Queue
from threading import Thread
from urllib.parse import urlparse, parse_qs
# from uuid import uuid4

# from pydub import exceptions as pydub_excpetions
from pydub import AudioSegment
from youtube_dl import YoutubeDL

from split_init import METADATA_PROVIDERS, ydl_opts
from utils import (split_song, time_to_seconds,
                   track_parser, tracks_parser,
                   update_time_change,
                   tracks_editor, ffmpeg_utils)
from utils.ffmpeg_utils import (is_same_length, get_length)

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

PYDUB_MAX_SIZE = 4 * 1024 * 1024
MAX_BITRATE = "256k"
OPUS_MAX_BITRATE = "160k"
ACODEC_SHORTCUTS = {
    'fdk': 'libfdk_aac -cutoff 18000',
    'fdk_aac': 'libfdk_aac -cutoff 18000',
    'aac': 'aac -cutoff 18000',
    'mp3': 'libmp3lame',
    'ogg': 'libvorbis',
    'flac': 'flac',
    'opus': 'libopus',
}
ACODEC_PROFILES = {
    'fdk_vbr': (ACODEC_SHORTCUTS['fdk'], '-vbr 5'),
    'fdk': (ACODEC_SHORTCUTS['fdk'], "-b:a {}".format(MAX_BITRATE)),
    'fdk_hq': (ACODEC_SHORTCUTS['fdk'], "-b:a 320k"),
    'aac_vbr': (ACODEC_SHORTCUTS['aac'], '-q:a 0'),
    'aac': (ACODEC_SHORTCUTS['aac'], "-b:a {}".format(MAX_BITRATE)),
    'aac_hq': (ACODEC_SHORTCUTS['aac'], "-b:a 320k"),
    'mp3_vbr': (ACODEC_SHORTCUTS['mp3'], '-q:a 0', 'mp3'),
    'mp3': (ACODEC_SHORTCUTS['aac'], "-b:a {}".format(MAX_BITRATE)),
    'ogg_vbr': (ACODEC_SHORTCUTS['ogg'], "-q:a 8"),
    'ogg': (ACODEC_SHORTCUTS['ogg'], "-b:a {}".format(MAX_BITRATE)),
    'flac': (ACODEC_SHORTCUTS['flac'], ""),
    'opus': (ACODEC_SHORTCUTS['opus'], "-b:a {}".format(OPUS_MAX_BITRATE)),
    'opus_vbr': (ACODEC_SHORTCUTS['opus'], "-b:a 128k"),
}
EXT_MAPPER = {
    'libfdk_aac': 'm4a',
    'fdk': 'm4a',
    'aac': 'm4a',
    'libmp3lame': 'mp3',
    'libvorbis': 'ogg',
    'ogg': 'ogg',
    'flac': 'flac',
    'libopus': 'opus'
}
FFMPEG_DEFAULT_CODEC = "aac"
FFMPEG_DEFAULT_EXT = "m4a"


def set_source_file_format(sf_format):
    ydl_opts['postprocessors'] = \
        [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': sf_format,
            'preferredquality': '0',
        }]


SOURCE_FILE_FORMAT = "wav"
# SOURCE_FILE_FORMAT = "flac"
ROLLBACK_SOURCE_FILE_FORMAT = "wav"
set_source_file_format(SOURCE_FILE_FORMAT)


def thread_func(album, tracks_start, queue, FOLDER, ARTIST, ALBUM, FILE_TYPE, TRK_TIMESKIP, FFMPEG_MODE):
    while not queue.empty():
        song_tuple = queue.get()
        split_song(album, tracks_start, song_tuple[0], song_tuple[1],
                   FOLDER, ARTIST, ALBUM, BITRATE, FILE_TYPE, TRK_TIMESKIP_F, TRK_TIMESKIP_R, FFMPEG_MODE)


def check_FFMpeg_codec(current_codec, rollback_codec):
    ffu = ffmpeg_utils()
    if not ffu.check_codec(codec_name=current_codec):
        print("{} is not supported by current FFMpeg!!".format(current_codec))
        print("Codec: {}".format(current_codec))
        print("FFMpeg: {}".format(ffu.ffmpeg_path))
        print("Thus, reverting the main source file format to default one! ({})".format(
            rollback_codec))
        return False
    else:
        return True


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
        help="Specify the bitrate of the export. Default: '{}'".format(
            MAX_BITRATE),
        default=MAX_BITRATE
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
    parser.add_argument(
        "--codec_info",
        help="Specify FFMpeg audio codec command. Default: None",
        dest="ffmpeg_acodec_info",
        default=""
    )
    parser.add_argument(
        "--profile",
        help="Define Lossy audio encoding method profiles: {}".format(
            ACODEC_PROFILES.keys()),
        dest="ffmpeg_profile",
        default="default"
    )
    parser.add_argument(
        "--ffmpeg-mode",
        help="When given, pydub is completely ignored and the script uses system ffmpeg. Default: No",
        dest="ffmpeg_mode",
        default='Yes'
    )

    args = parser.parse_args()
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
    BITRATE = args.bitrate.lower()
    TRK_TIMESKIP_F = int(args.trk_timeskip_f)
    TRK_TIMESKIP_R = int(args.trk_timeskip_r)
    TRACKS_FILE_NAME = args.tracks

    FFMPEG_PROFILE = args.ffmpeg_profile.lower()
    if FFMPEG_PROFILE == 'default' or FFMPEG_PROFILE == '':
        FFMPEG_CODEC_NAME = FFMPEG_DEFAULT_CODEC
        ACODEC_INFO = ACODEC_SHORTCUTS['aac']
    else:
        FFMPEG_CODEC_NAME = ACODEC_SHORTCUTS[FFMPEG_PROFILE.split('_')[0]].split(' ')[
            0]
    FFMPEG_EXT_NAME = EXT_MAPPER[FFMPEG_CODEC_NAME]

    try:
        ACODEC_INFO = ACODEC_SHORTCUTS[args.ffmpeg_acodec_info].lower()
    except KeyError:
        ACODEC_INFO = args.ffmpeg_acodec_info.lower()
    if ACODEC_INFO:
        FFMPEG_CODEC_NAME = ACODEC_INFO.split(' ')[0]
        FFMPEG_EXT_NAME = EXT_MAPPER[FFMPEG_CODEC_NAME]

    # Check codec exists!
    # TODO: Implement more elegant rollback codec selector later.
    # from utils.ffmpeg_utils import ffmpeg_utils

    # Check up the source format. Default is flac but rollback
    # as wav.
    if not check_FFMpeg_codec(SOURCE_FILE_FORMAT, ROLLBACK_SOURCE_FILE_FORMAT):
        set_source_file_format(ROLLBACK_SOURCE_FILE_FORMAT)

    # Check up given output codec exists!
    # rollback is 'aac' at this moment.
    if not check_FFMpeg_codec(FFMPEG_CODEC_NAME, 'aac'):
        ACODEC_INFO = ACODEC_SHORTCUTS['aac']
        FFMPEG_CODEC_NAME = 'aac'

    FFMPEG_MODE = True
    if 'n' in args.ffmpeg_mode.lower():
        FFMPEG_MODE = False

    if FFMPEG_MODE:
        FILE_TYPE = FFMPEG_EXT_NAME
    else:
        FILE_TYPE = args.output_format.lower()

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

    # Let's check up if tracks file exists!!
    # if not, open an editor window
    if not os.path.isfile(TRACKS_FILE_NAME):
        app = QApplication(sys.argv)
        app.setApplicationName("split.py - Tracks Editor")
        te = tracks_editor(trk_fname=TRACKS_FILE_NAME, duration=DURATION)
        app.exec_()
        te.close()

    print("Parsing " + TRACKS_FILE_NAME)
    tracks_start, tracks_titles = \
        tracks_parser(TRACKS_FILE_NAME, DRYRUN, DURATION)

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
        FILENAME = "{}.{}".format(video_id, SOURCE_FILE_FORMAT)
        if not os.path.isfile(FILENAME):
            print("Downloading video from YouTube")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(['http://www.youtube.com/watch?v=' + video_id])
            print("\nConversion complete")
        else:
            print("Found matching file")
        print("Loading audio file")

        if os.stat(FILENAME).st_size < PYDUB_MAX_SIZE:
            album = AudioSegment.from_file(FILENAME, SOURCE_FILE_FORMAT)
        else:
            album = FILENAME
            FFMPEG_MODE = True

    else:
        print("Loading audio file")
        file_ext = os.path.splitext(FILENAME)[-1].replace('.', '').lower()
        f_size = os.stat(FILENAME).st_size
        if file_ext != SOURCE_FILE_FORMAT:
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
        print("current output type: ", FILE_TYPE)
        if album_ext != FILE_TYPE:
            file_basename = os.path.splitext(os.path.realpath(album))[0]

            if FFMPEG_PROFILE == 'default':
                # Setting up audio codec parameters
                if ACODEC_INFO:
                    acodec_param = "-acodec {}".format(ACODEC_INFO)
                else:
                    acodec_param = ''

                # Setting up bitrate parameters
                if BITRATE.lower().replace('k', '').isnumeric():
                    bit_rate_param = "-b:a {}".format(BITRATE)
                elif BITRATE.lower() == 'vbr':
                    if 'libfdk_aac' in acodec_param:
                        bit_rate_param = "-vbr 5"
                    else:
                        bit_rate_param = "-q:a 0"
            else:
                acodec_param = '-acodec {}'.format(
                    ACODEC_PROFILES[FFMPEG_PROFILE][0])
                bit_rate_param = ACODEC_PROFILES[FFMPEG_PROFILE][1]

            ffmpeg_params_str = ' '.join([acodec_param, bit_rate_param])

            print("Converting the album file to designated output file.")
            source_audio_name = "{}.{}".format(
                file_basename, SOURCE_FILE_FORMAT)
            converted_audio_name = "{}.{}".format(file_basename, FILE_TYPE)

            if os.path.exists(converted_audio_name) and is_same_length(source_audio_name, converted_audio_name):
                print("Same file exists!! Skipping conversion!!")
                print(
                    "Delete the previous converted long file to make sure newer encoding.")
            else:
                orig_stream = ffmpeg_utils(
                    input_file=source_audio_name,
                    output_file=converted_audio_name,
                    params_str=ffmpeg_params_str
                )
                orig_stream.set_global_options_str('-y -hide_banner')
                orig_stream.run()

            # print("Removing the source file... to save space.")
            # os.remove(album)
            album = converted_audio_name

        tracks_start.append(get_length(album) * 1000)
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
