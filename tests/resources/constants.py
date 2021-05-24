#constants.py

#UPDATE_HTML_FILES_CAPTURED
#boolean (default: 'False')
#Mark 'False' to not update your HTML files, from Amazon and Wikipedia by running 'html_file_downloader.py'.
#Mark 'True' to update your HTML files, from Amazon and Wikipedia by running 'html_file_downloader.py'.
#The 'HTML_file_downloader.py' gets newest HTMLs to be used in offline tests and, stores all old HTMLs in a proper datetimed subfolder.
UPDATE_HTML_FILES_CAPTURED = False

#DO_ONLINE_TESTS
#boolean (default: 'False')
#Mark 'False' to run only offline tests, and 'True' to run online tests. 
#If you mark 'True', the online tests will consume two things from you:
#1- Your internet bandwith;
#2- Your accesses in Amazon.
DO_ONLINE_TESTS = False

#RESPONSES_IN_HTML_FILES_DIR_PATH
#string (default: './tests/resources/html_files_captured/latest_html_files_captured/')
#Points to directory (folder) that contains all *.html responses exported from Amazon and Wikipedia.
#The HTML are used in offline tests, helping in simulate the responses.
#The folder contains only HTML from 3 sites used in tests (Amazon, Wikipedia).
RESPONSES_IN_HTML_FILES_DIR_PATH = './tests/resources/html_files_captured/latest_html_files_captured/'

#TRACK_FILENAME_INFO
#Name of tha file that contains tracks and times information.
TRACK_FILENAME = 'tracks.txt'

#AMAZON TEST INFO
#Relation of Amazon Urls to be accessed
AMAZON_URLS = {
    'with_song_table' : 'https://www.amazon.com/Dogs-Eating-blink-182/dp/B00B054FFA',
    'without_song_table' : 'https://www.amazon.com/p/feature/rzekmvyjojcp6uc',
    #'with_404' : 'https://www.amazon.com/404',
}

WIKIPEDIA_URLS = {
    'with_song_table' : 'https://en.wikipedia.org/wiki/Dogs_Eating_Dogs',
    'without_song_table' : 'https://en.wikipedia.org/wiki/Wikipedia:About',
    #'with_404' : '',
}

VALID_URLS = {
    'amazon' : 'https?://(?:\w+\.)?amazon\..*/.*',
    'wikipedia' : 'https?://(?:\w+\.)?wikipedia\..*/.*',
}



