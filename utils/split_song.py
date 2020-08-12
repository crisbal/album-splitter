from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

import string
import os
import math
import subprocess as sbp
from shutil import which


TAG_formats = ['mp3', 'mp4', 'm4a']
# This could be 'libfdk_aac' if you want
MP4_DEFAULT_CODEC = 'aac'

cmd_string_split = 'ffmpeg -y -i "{tr}" -acodec copy -ss {st} -to {en} "{nm}"'


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
    audio_file_ext = os.path.splitext(audio_path)[-1].lower()

    if audio_file_ext == '.mp3':
        return MP3(audio_path).info.length
    elif audio_file_ext == '.mp4' or audio_file_ext == '.m4a':
        return MP4(audio_path).info.length


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
            song = EasyID3(track_path)
        elif output_format == "mp4" or output_format == "m4a":
            song = EasyMP4(track_path)

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
        return

    if output_format == 'm4a':
        album[start:][:duration].export(
            track_path, format='mp4', bitrate=bitrate, codec=MP4_DEFAULT_CODEC)
    else:
        album[start:][:duration].export(
            track_path, format=output_format, bitrate=bitrate)

    # Let's tag!
    TAG_it(output_format, track_path, artist, album_title, index, track)


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
    if os.path.exists(track_path) and audio_length_test(track_path, duration*1000):
        print("Split already exists!! Passing!")
        return

    # Now let's call system ffmpeg to split it!!
    command = cmd_string_split.format(
        tr=album_file, st=start, en=end, nm=track_path)
    sbp.call(command, shell=True)

    TAG_it(output_format, track_path, artist, album_title, index, track)


# Main interface...
def split_song(album, tracks_start, index, track, folder='.',
               artist=None, album_title=None, bitrate=None, output_format="mp3",
               timeskip_front=0, timeskip_end=0, FFMpeg_mode=False):

    if FFMpeg_mode:
        return split_song_FFMpeg(album, tracks_start, index, track, folder,
                                 artist, album_title, bitrate, output_format,
                                 timeskip_front, timeskip_end)
    else:
        return split_song_pydub(album, tracks_start, index, track, folder,
                                artist, album_title, bitrate, output_format,
                                timeskip_front, timeskip_end)
