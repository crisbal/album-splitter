# Parse a Wikipedia page to get the tracks' details
#
# AUTHOR: https://github.com/inondle

from urllib.request import build_opener
from bs4 import BeautifulSoup

from utils import write_tracks_to_file

VALID_URL = "https?://(?:\w+\.)?wikipedia\..*/.*"


def lookup(url, tracks_filename):
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Album-Splitter')]
    page_html = opener.open(url).read()
    soup = BeautifulSoup(page_html, 'html.parser')
    song_table = soup.find_all(class_='tracklist')
    if not song_table:
        return None

    rows = song_table[0].find_all('tr')
    # first line of table is a headerrows[0]
    number_of_columns = find_number_of_columns(rows[0])
    del(rows[0])

    track_titles = []
    track_times = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds) == number_of_columns:
            try:
                track_titles.append(tds[1].get_text())
            except TypeError:
                break
            track_times.append(tds[number_of_columns-1].get_text())
    write_tracks_to_file(track_times, track_titles, tracks_filename)
    return True


def find_number_of_columns(table_header):
    return len(table_header.find_all('th'))
