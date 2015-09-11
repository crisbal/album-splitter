from pydub import AudioSegment
import eyed3
import os, sys
import re, argparse, urlparse
import youtube_dl

##youtube_dl configuration
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
        sys.stdout.write('\tDownloading video | ETA: ' + str(d["eta"]) + " seconds")
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
  if len(parts) == 3: #h:m:s
    seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
  elif len(parts) == 2: #m:s
    seconds = int(parts[0])*60 + int(parts[1])

  return seconds



def findTrackSection(lines):
	while lines:
		line = lines[0]
		if 'Track listing[edit]' in line:
			return True
		else:
			del lines[0]
	return False


def findTrackTable(lines):
	while lines:
		line = lines[0]
		if 'No.' in line:
			del lines[0]
			return True
		else:
			del lines[0]
	return False


def writeWikiToTracks(track_times, track_titles):
	track_file = open('tracks.txt', 'w')
	text = ""
	for num in range(len(track_times)):
		text += (track_times[num] + ' - ' + track_titles[num] + '\n')
	track_file.seek(0)
	track_file.write(text)
	track_file.truncate()
	track_file.close()


def wikiLookup(url):
	os.system('lynx -dump -nolist \''+ url + '\' > ./.tmp.txt')
	wiki_file = open('.tmp.txt')
	lines = wiki_file.readlines()
	track_times = []
	track_titles = []
	if findTrackSection(lines) and findTrackTable(lines):
		while lines:
			line = lines[0]
			read_title = re.search('\"[^\"]*\"', line)
			read_time = re.search('\d*:\d\d', line)
			if not read_time:
				break
			track_times.append(read_time.group(0))
			track_titles.append(read_title.group(0))
			del lines[0]
	writeWikiToTracks(track_times, track_titles)
	os.remove('./.tmp.txt')


if __name__ == "__main__":
  print("Starting")


  #arg parsing
  parser = argparse.ArgumentParser(description='Split a single-file mp3 Album into its tracks.')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-mp3", help="The .mp3 file you want to split.", metavar="mp3_file")
  group.add_argument("-yt", help="The YouTube video url you want to download and split.", metavar="youtube_url")
  parser.add_argument("-a", "--artist", help="Specify the artist that the mp3s will be ID3-tagged with. Default: no tag", default=None)
  parser.add_argument("-A",  "--album", help="Specify the album that the mp3s will be ID3-tagged with. Default: no tag", default=None)
  parser.add_argument("-t", "--tracks", help="Specify the tracks file. Default: tracks.txt", default="tracks.txt")
  parser.add_argument("-f", "--folder", help="Specify the folder the mp3s will be put in. Default: splits/", default="splits")
  parser.add_argument("-u", "--wikiurl", help="URL of wikipedia page with album track list table.", default=None)

  args = parser.parse_args()
  TRACKS_FILE =  args.tracks
  FILENAME = args.mp3
  YT_URL = args.yt
  ALBUM = args.album
  ARTIST = args.artist
  WIKI_URL = args.wikiurl

  if ALBUM and ARTIST and args.folder == "splits":
    FOLDER = ARTIST + " - " + ALBUM
  else:
    FOLDER = args.folder

  if WIKI_URL:
    wikiLookup(WIKI_URL)

  #create destination folder
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
    url_data = urlparse.urlparse(YT_URL)
    query = urlparse.parse_qs(url_data.query)
    videoID = query["v"][0]
    FILENAME = videoID + ".mp3"
    #opts=['--extract-audio','--audio-format', 'mp3', '--audio-quality', '0', YT_URL.decode('utf-8'), '-o', FILENAME.decode('utf-8')]
    print("Downloading video from YouTube")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download(['http://www.youtube.com/watch?v=' + videoID])
    print("\nConversion to mp3 complete")

  print("Loading .mp3 file")
  album = AudioSegment.from_file(FILENAME, 'mp3')
  print(".mp3 file loaded")

  tracksStarts.append(len(album)) #we need this for the last track/split
  tracksTitles.append("END") 

  print("Starting to split")
  for i, track in enumerate(tracksTitles):
    if i != len(tracksTitles)-1:
      print("\t" + str(i+1) + ") " + track)
      start = tracksStarts[i]
      end = tracksStarts[i+1]
      duration = end-start
      album[start:][:duration].export( FOLDER + "/" + track + ".mp3", format="mp3")

      print("\t\tTagging")
      song = eyed3.load(FOLDER + "/" + track + ".mp3")
      if ARTIST:
        song.tag.artist = ARTIST.decode('utf-8')
      if ALBUM:
        song.tag.album = ALBUM.decode('utf-8')

      song.tag.title = track.decode('utf-8')
      song.tag.track_num = i+1
      song.tag.save()
  print("All Done")


