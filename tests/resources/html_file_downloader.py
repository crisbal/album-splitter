import os
import re
import datetime
#import requests
from urllib.request import build_opener

from resources import constants

def write_html_file(page_name, data_to_be_saved, iso_date):
    for specific_dir in ['latest_html_files_captured', iso_date]:
        filename = os.path.normpath(
            './tests/resources/html_files_captured/'
            + specific_dir
            + '/'
            + page_name 
            + '.html')
        dirpath = os.path.dirname(filename)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        print('New HTML file downloaded in: ', filename)
        with open(filename, 'w') as file_html:
            file_html.write(page_html)


def access_html_from(url):
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Album-Splitter')]
    page_html = opener.open(url).read()
    return page_html.decode()


def domain_from(url):
    for domain, url_regex in constants.VALID_URLS.items():
        pattern = re.compile(url_regex)
        if pattern.match(url):
            return domain

iso_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
for d in [constants.AMAZON_URLS, constants.WIKIPEDIA_URLS]:
    for key, url in d.items():
        site_name = domain_from(url)
        if site_name:
            file_name = site_name + '_' + key
            page_html = access_html_from(url)
            write_html_file(file_name, page_html, iso_date)
    
    
    
