# Parse an Amazon page to get the tracks' details
#
# AUTHOR: https://github.com/crisbal

from urllib.request import build_opener
from bs4 import BeautifulSoup
import splitutil
import re


def lookup(url):
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Album-Splitter')]
    page_html = opener.open(url).read()
    page = BeautifulSoup(page_html, 'html.parser')
    song_table = page.find(id='dmusic_tracklist_content')
    if not song_table:
        return None

    song_lines = song_table.findAll('tr')
    # first line of table is a header
    del(song_lines[0])
    track_titles = []
    track_times = []
    for line in song_lines:
        track_titles.append(line.find(attrs={'class': 'TitleLink'}).text.strip())
        track_times.append(line.find(id=re.compile("dmusic_tracklist_duration.*")).text.strip())
    splitutil.writeTracksToFile(track_times, track_titles)
    return True
