from mutagen.easyid3 import EasyID3


def split_song(album, tracks_start, index, track, folder='.', artist=None, album_title=None):
    print("\t{}) {}".format(str(index+1), track))
    start = tracks_start[index]
    end = tracks_start[index+1]
    duration = end-start
    track_path = '{}/{:02d} - {}.mp3'.format(folder, index+1, track)
    album[start:][:duration].export(track_path, format="mp3")

    print("\t\tTagging")
    song = EasyID3(track_path)
    if artist:
            song['artist'] = artist
    if album_title:
            song['album'] = album_title
    song['title'] = track
    song['tracknumber'] = str(index+1)
    song.save()
