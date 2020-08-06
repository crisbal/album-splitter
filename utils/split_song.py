from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
import string

TAG_formats = ['mp3', 'mp4']

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
    return valid_name.replace('  ',' ')

def split_song(album, tracks_start, index, track, folder='.', artist=None, album_title=None, bitrate=None, output_format="mp3", timeskip_front=0, timeskip_end=0):
    print("\t{}) {}".format(str(index+1), track))
    start = tracks_start[index]+timeskip_front
    end = tracks_start[index+1]-timeskip_end
    duration = end - start
    track_path = '{}/{:02d} - {}.{}'.format(folder, index+1, fname_check(track), output_format)
    if output_format == 'm4a':
        album[start:][:duration].export(track_path, format='mp4', bitrate=bitrate, codec='aac')
    else:
        album[start:][:duration].export(track_path, format=output_format, bitrate=bitrate)


    if output_format in TAG_formats:
        print("\t\tTagging")
        if output_format == "mp3":
            song = EasyID3(track_path)
        elif output_format == "mp4":
            song = EasyMP4(track_path)
        if artist:
            song['artist'] = artist
        if album_title:
            song['album'] = album_title
        song['title'] = track
        song['tracknumber'] = str(index+1)
        song.save()
    else:
        print("Output format doesn't seem to support ID3. Skipping Tagging.")
