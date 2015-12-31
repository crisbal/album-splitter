# Parse a Wikipedia page to get the tracks' details
#
# AUTHOR: https://github.com/inondle

from urllib.request import build_opener
from bs4 import BeautifulSoup
import splitutil
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
    # first line of table is a header
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
    splitutil.writeTracksToFile(track_times, track_titles)
    return True


def extract_title(track_line):
    title = None
    title_row = track_line.contents[3]
    if len(title_row.contents) > 1 and not title_row('span'):
        # Get title from a link
        title = title_row.contents[1].contents[0]
    else:
        title = title_row.contents[0]
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
