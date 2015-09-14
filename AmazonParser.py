# Parse an Amazon page to get the tracks' details
#
# AUTHOR: https://github.com/crisbal

import urllib2
from bs4 import BeautifulSoup
import re

def lookup(url):
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', 'Album-Splitter')]
  page_html = opener.open(url).read()
  page = BeautifulSoup(page_html, 'html.parser')
  song_table = page.find(id='dmusic_tracklist_content')
  if not song_table:
    return None

  song_lines = song_table.findAll('tr')
  #first line of table is a header
  del(song_lines[0])
  track_titles = []
  track_times = []
  for line in song_lines:
    track_titles.append(line.find(attrs={'class': 'TitleLink'}).text.strip())
    track_times.append(line.find(id=re.compile("dmusic_tracklist_duration.*")).text.strip())
  writeTracksToFile(track_times, track_titles)
  return True

#Thanks https://github.com/inondle
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

#Thanks https://github.com/inondle
def writeTracksToFile(track_times, track_titles):
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