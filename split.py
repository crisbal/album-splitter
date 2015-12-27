from pydub import AudioSegment
from urllib.parse import urlparse, parse_qs
from mutagen.easyid3 import EasyID3
from youtube_dl import YoutubeDL
import os
import sys
import re
import argparse
import WikiParser
import AmazonParser

# youtube_dl configuration


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'downloading':
        sys.stdout.write('\r\033[K')
        sys.stdout.write('\tDownloading video | ETA: {} seconds'.format(str(d["eta"])))
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.write('\tDownload complete\n\tConverting video to mp3')
        sys.stdout.flush()

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '0',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}


def timeToSeconds(time):
    parts = time.split(":")
    seconds = None
    if len(parts) == 3:  # h:m:s
        seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    elif len(parts) == 2:  # m:s
        seconds = int(parts[0])*60 + int(parts[1])
    return seconds

if __name__ == "__main__":
    print("Starting")

    # arg parsing
    parser = argparse.ArgumentParser(description='Split a single-file mp3 Album into its tracks.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-mp3", help="The .mp3 file you want to split.", metavar="mp3_file")
    group.add_argument("-yt", help="The YouTube video url you want to download and split.", metavar="youtube_url")
    parser.add_argument("-a", "--artist", help="Specify the artist that the mp3s will be ID3-tagged with. Default: no tag", default=None)
    parser.add_argument("-A",  "--album", help="Specify the album that the mp3s will be ID3-tagged with. Default: no tag", default=None)
    parser.add_argument("-t", "--tracks", help="Specify the tracks file. Default: tracks.txt", default="tracks.txt")
    parser.add_argument("-f", "--folder", help="Specify the folder the mp3s will be put in. Default: splits/", default="splits")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-wiki", "--wikipedia", help="Get tracks details from Wikipedia: URL of a Wikipedia's page with an album track list table.", default=None)
    group.add_argument("-amz", "--amazon", help="Get tracks details from Amazon: URL of the Amazon's page of the album.", default=None)

    args = parser.parse_args()
    TRACKS_FILE = args.tracks
    FILENAME = args.mp3
    YT_URL = args.yt
    ALBUM = args.album
    ARTIST = args.artist
    WIKI_URL = args.wikipedia
    AMZ_URL = args.amazon

    if ALBUM and ARTIST and args.folder == "splits":
        FOLDER = '{} - {}'.format(ARTIST, ALBUM)
    else:
        FOLDER = args.folder

    if WIKI_URL:
        print("Parsing Wiki: {}".format(WIKI_URL))
        if not WikiParser.lookup(WIKI_URL):
            print("Can't find a track list in the provided Wiki Page. Shutting Down.")
            exit()
    elif AMZ_URL:
        print("Parsing AMZ: {}".format(AMZ_URL))
        if not AmazonParser.lookup(AMZ_URL):
            print("Can't find a track list in the provided Amazon Page. Shutting Down.")
            exit()

    # create destination folder
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)

    tracksStarts = []
    tracksTitles = []

    regex = re.compile("(?P<start>.+)\s*\-\s*(?P<title>.+)")

    print("Parsing " + TRACKS_FILE)
    with open(TRACKS_FILE) as tracksF:
        for i, line in enumerate(tracksF):
            m = regex.match(line)

            tStart = timeToSeconds(m.group('start').strip())
            tTitle = m.group('title').strip()

            tracksStarts.append(tStart*1000)
            tracksTitles.append(tTitle)
    print("Tracks file parsed")

    if YT_URL:
        url_data = urlparse(YT_URL)
        query = parse_qs(url_data.query)
        videoID = query["v"][0]
        FILENAME = videoID + ".mp3"
        if not os.path.isfile(FILENAME):
                print("Downloading video from YouTube")
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download(['http://www.youtube.com/watch?v=' + videoID])
                print("\nConversion to mp3 complete")
        else:
                print("Found matching mp3 file")

    print("Loading .mp3 file")
    album = AudioSegment.from_file(FILENAME, 'mp3')
    print(".mp3 file loaded")

    tracksStarts.append(len(album))  # we need this for the last track/split
    tracksTitles.append("END")

    print("Starting to split")
    for i, track in enumerate(tracksTitles):
        if i != len(tracksTitles)-1:
            print("\t{}) {}".format(str(i+1), track))
            start = tracksStarts[i]
            end = tracksStarts[i+1]
            duration = end-start
            track_path = '{}/{}.mp3'.format(FOLDER, track)
            album[start:][:duration].export(track_path, format="mp3")

            print("\t\tTagging")
            song = EasyID3(track_path)
            if ARTIST:
                    song['artist'] = ARTIST
            if ALBUM:
                    song['album'] = ALBUM
            song['title'] = track
            song['tracknumber'] = str(i+1)
            song.save()
    print("All Done")
