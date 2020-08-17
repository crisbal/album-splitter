import string
import os
import math
from shutil import which

from .ffmpeg_utils import ffmpeg_utils
from .ffmpeg_utils import get_length

TAG_formats = ['mp3', 'mp4', 'm4a', 'ogg', 'flac', 'opus']


def fname_check(name_str, spacer='_'):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    valid_name = ''
    for c in name_str:
        if c in valid_chars:
            valid_name += c
        elif c == "&":
            valid_name += ' and '
        else:
            valid_name += spacer
    return valid_name.replace('  ', ' ')


def get_audio_length(audio_path):
    return get_length(audio_path)


def audio_length_test(audio_path, duration):
    if not os.path.exists(audio_path):
        print("Given audio path not found!!")
        raise FileNotFoundError

    audio_length = get_audio_length(audio_path)
    return math.isclose(audio_length * 1000, duration, rel_tol=0.03)


def TAG_it(output_format, track_path, artist, album_title, index, track):
    if output_format in TAG_formats:
        print("\t\tTagging")
        if output_format == "mp3":
            from mutagen.easyid3 import EasyID3
            song = EasyID3(track_path)
        elif output_format == "mp4" or output_format == "m4a":
            from mutagen.easymp4 import EasyMP4
            song = EasyMP4(track_path)
        elif output_format == 'ogg':
            from mutagen import File as mFile
            song = mFile(track_path)
        elif output_format == 'flac':
            from mutagen.flac import FLAC
            song = FLAC(track_path)
        else:
            from mutagen import File as mFile
            song = mFile(track_path)

        if artist:
            song['artist'] = artist
        if album_title:
            song['album'] = album_title
        song['title'] = track
        song['tracknumber'] = str(index + 1)
        song.save()
    else:
        print("Tagging is not supported on {} format at this moment.".format(
            output_format))
        return


def split_song_pydub(album, tracks_start, index, track, folder='.',
                     artist=None, album_title=None, bitrate=None, output_format="mp3",
                     timeskip_front=0, timeskip_end=0):
    print("\t{}) {}".format(str(index + 1), track))
    start = tracks_start[index] + timeskip_front
    end = tracks_start[index + 1] - timeskip_end
    duration = end - start
    track_path = '{}/{:02d} - {}.{}'.format(
        folder, index + 1, fname_check(track), output_format)

    # ignore if the splitted file already exists!!
    if os.path.exists(track_path) and audio_length_test(track_path, duration):
        print("Split already exists!! Passing!")
    else:
        if output_format == 'm4a':
            album[start:][:duration].export(
                track_path, format='mp4', bitrate=bitrate, codec=MP4_DEFAULT_CODEC)
        else:
            album[start:][:duration].export(
                track_path, format=output_format, bitrate=bitrate)

    return track_path


def split_song_FFMpeg(album_file, tracks_start, index, track, folder='.',
                      artist=None, album_title=None, bitrate=None, output_format="mp3",
                      timeskip_front=0, timeskip_end=0):

    if which("ffmpeg") is None:
        raise EnvironmentError("We need ffmpeg in your path!!")

    print("\t{}) {}".format(str(index + 1), track))
    start = (tracks_start[index] + timeskip_front) / 1000
    end = (tracks_start[index + 1] - timeskip_end) / 1000
    duration = end - start
    track_path = '{}/{:02d} - {}.{}'.format(
        folder, index + 1, fname_check(track), output_format)

    # ignore if the splitted file already exists!!
    if os.path.exists(os.path.realpath(track_path)) and audio_length_test(os.path.realpath(track_path), duration * 1000):
        print("Split already exists!! Passing!")

    else:
        # Now let's call system ffmpeg to split it!!
        stream = ffmpeg_utils()
        stream.set_input_file(album_file)
        stream.set_output_file(track_path)
        stream.set_params(
            acodec="copy",
            ss=str(start),
            to=str(end)
        )
        stream.run()

    return track_path

# Main interface...


def split_song(album, tracks_start, index, track, folder='.',
               artist=None, album_title=None, bitrate=None, output_format="mp3",
               timeskip_front=0, timeskip_end=0, FFMpeg_mode=False):

    if FFMpeg_mode:
        track_path = split_song_FFMpeg(album, tracks_start, index, track, folder,
                                       artist, album_title, bitrate, output_format,
                                       timeskip_front, timeskip_end)
    else:
        track_path = split_song_pydub(album, tracks_start, index, track, folder,
                                      artist, album_title, bitrate, output_format,
                                      timeskip_front, timeskip_end)

    if os.path.exists(track_path):
        TAG_it(output_format, track_path, artist, album_title, index, track)
