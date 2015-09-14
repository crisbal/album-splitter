from pydub import AudioSegment
from bs4 import BeautifulSoup
import eyed3
import os, sys
import re, argparse, urlparse
import youtube_dl
import urllib2

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


def updateTimeChange(time_elapsed, track_time):
  elapsed_h = int(time_elapsed[:1])
  elapsed_m = int(time_elapsed[2:4])
  elapsed_s = int(time_elapsed[5:7])
  # 1:23 -> 01:23
  if(len(track_time) == 4):
   track_time = "0" + track_time
  #get track length
  track_m = int(track_time[:2])
  track_s = int(track_time[3:])
  #add track length to elapsed time
  elapsed_m = elapsed_m + track_m
  elapsed_s = elapsed_s + track_s

  if elapsed_m >= 60:
    elapsed_m -= 60
    elapsed_h += 1
  elif elapsed_s >= 60:
    elapsed_s -= 60
    elapsed_m +=1

  str_m = ""
  str_s = ""
  #1 -> 01 
  if elapsed_m < 10:
    str_m = "0" + str(elapsed_m)
  else:
    str_m = str(elapsed_m)

  if elapsed_s < 10:
    str_s = "0" + str(elapsed_s)
  else:
    str_s = str(elapsed_s)

  return str(elapsed_h) + ':' + str_m + ':' + str_s 
  

def writeWikiToTracks(track_times, track_titles):
  track_file = open('tracks.txt', 'w')
  time_elapsed = "0:00:00"
  text = ""
  for num in range(len(track_times)):
    text += (time_elapsed + ' - ' + str(track_titles[num]) + '\n')
    time_elapsed = updateTimeChange(time_elapsed, track_times[num])

  track_file.seek(0)
  track_file.write(text)
  track_file.truncate()
  track_file.close()


def extract_from_unicode(title):
  u = title.encode('utf-8', 'ignore')
  return re.findall('"([^"]*)"', u)[0]

def extract_linked_title(linked_title):
   l = linked_title.contents[3].contents[1].contents[0]
   return l

def extract_title(track_line):
  if(len(track_line.contents[3].contents) > 1):
    #title is linked...
    title = extract_linked_title(track_line)
  else:
    title = extract_from_unicode(track_line.contents[3].contents[0])
  return title

def wikiLookup(url):
  page_html = urllib2.urlopen(url).read()
  soup = BeautifulSoup(page_html, 'html.parser')
  song_table = soup.find_all(class_='tracklist')
  if not song_table:
    return None

  song_lines = song_table[0].find_all('tr')
  #first line of table is a header
  del(song_lines[0])
  track_titles = []
  track_times = []
  for line in song_lines:
    if(line.find_all('div')):
      break
    track_titles.append(extract_title(line))
    track_times.append(line.contents[5].contents[0])
  writeWikiToTracks(track_times, track_titles)

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
  parser.add_argument("-w", "--wikiurl", help="URL of wikipedia page with album track list table.", default=None)

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
    print("Parsing Wiki: " + WIKI_URL)
    if not wikiLookup(WIKI_URL):
      print("Can't find a track list in the provided Wiki Page. Shutting Down.")
      exit()

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


