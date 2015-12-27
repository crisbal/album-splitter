# Parse a Wikipedia page to get the tracks' details
#
# AUTHOR: https://github.com/inondle

from urllib.request import build_opener
from bs4 import BeautifulSoup

import re

def lookup(url):
  opener = build_opener()
  opener.addheaders = [('User-agent', 'Album-Splitter')]
  page_html = opener.open(url).read()
  soup = BeautifulSoup(page_html, 'html.parser')
  song_table = soup.find_all(class_='tracklist')
  if not song_table:
    return None

  rows = song_table[0].find_all('tr')
  #first line of table is a header
  length_column = find_length_column(rows[0])
  del(rows[0])
  track_titles = []
  track_times = []
  for row in rows:
    try:
        track_titles.append(extract_title(row))
    except(TypeError):
        break
    track_times.append(row.contents[length_column].contents[0])
  writeTracksToFile(track_times, track_titles)
  return True

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

  return '{}:{}:{}'.format(str(elapsed_h), str_m, str_s)

  

def writeTracksToFile(track_times, track_titles):
  track_file = open('tracks.txt', 'w')
  time_elapsed = "0:00:00"
  text = ""
  for title, time in zip(track_titles, track_times):
    text += '{} - {}\n'.format(time_elapsed, str(title))
    time_elapsed = updateTimeChange(time_elapsed, time)

  track_file.seek(0)
  track_file.write(text)
  track_file.truncate()
  track_file.close()


def extract_from_unicode(title):
  return re.findall('"([^"]*)"', title)[0]

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

def find_length_column(table_header):
  i = 0
  for child in table_header.contents:
    i += 1
    if child == '\n':
      continue
    if 'Length' in child.contents:
      break
  return i-1


