from pydub import AudioSegment
import re

def timeToSeconds(time):
  parts = time.split(":")

  seconds = None
  if len(parts) == 3: #h:m:s
    seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
  elif len(parts) == 2: #m:s
    seconds = int(parts[0])*60 + int(parts[1])
  
  return seconds


if __name__ == "__main__":
  tracksStarts = []
  tracksTitles = []

  regex = re.compile("(?P<start>.+)\s*\-\s*(?P<title>.+)")

  with open('tracks.txt') as tracksF:
    for i, line in enumerate(tracksF):
      m = regex.match(line)
      
      tStart = timeToMillisec(m.group('start').strip())
      tTitle = m.group('title').strip()

      tracksStarts.append(tStart)
      tracksTitles.append(tTitle) 


  print(tracksStarts)

  """song = AudioSegment.from_mp3("album.mp3")


  print(len(song)/1000)


  song[:208*1000].export("track1.mp3", format="mp3")

  song[(208*1000):][:(418-208)*1000].export("track2.mp3", format="mp3")"""