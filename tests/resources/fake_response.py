#fake_response.py

import unittest

import requests
from urllib.parse import urlparse
import os.path
from io import BytesIO

from resources import constants

#Return a fake response from a loaded json filesystem by url_path
def fake_requests_get(url):
    
    root_domain = urlparse(url).hostname.split('.')[1]
    kind_of_file = ''
    
    for rd, d in [('amazon', constants.AMAZON_URLS),('wikipedia', constants.WIKIPEDIA_URLS)]:
        if root_domain == rd:
            for kind, site in d.items():
                if url == site:
                    kind_of_file = kind
    
    resource_file = os.path.normpath(
        constants.RESPONSES_IN_HTML_FILES_DIR_PATH
        + root_domain
        + '_'
        + kind_of_file
        + '.html')
    faked_response = None
    
    with open(resource_file, mode='rb') as f:
        data = f.read()
        faked_response = BytesIO(data)
    return faked_response
