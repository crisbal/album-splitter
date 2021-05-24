#test_Wikipedia.py
#run this command to test all: 'python3 -m unittest discover -s tests -v'

import unittest
from unittest.mock import patch

from urllib.request import OpenerDirector
from http.client import HTTPResponse

from MetaDataProviders import Wikipedia
from resources import constants
from resources import fake_response


class TestRepo(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.module_Wikipedia = Wikipedia
        

    def test_Wikipedia_VALID_URL(self):
        self.assertEqual(self.module_Wikipedia, Wikipedia)
        self.assertEqual(type(self.module_Wikipedia), type(Wikipedia))
        self.assertEqual(self.module_Wikipedia.VALID_URL, constants.VALID_URLS['wikipedia'])
        self.assertEqual(self.module_Wikipedia.VALID_URL, Wikipedia.VALID_URL)


    def test_Wikipedia_lookup(self):
        with_song_table = constants.WIKIPEDIA_URLS['with_song_table']
        without_song_table = constants.WIKIPEDIA_URLS['without_song_table']
        #with_404 = constants.WIKIPEDIA_URLS['url_with_404']
        
        tracks_filename = constants.TRACK_FILENAME

        with patch('http.client.HTTPResponse.read') as mocked_read:
            with patch('urllib.request.OpenerDirector.open', side_effect = fake_response.fake_requests_get) as mocked_response:
                self.assertEqual(self.module_Wikipedia.lookup(with_song_table, tracks_filename), True)
                self.assertEqual(self.module_Wikipedia.lookup(without_song_table, tracks_filename), None)
                #self.assertRaises(HTTPError, self.module_Wikipedia.lookup(with_404, tracks_filename))

        if constants.DO_ONLINE_TESTS:
            self.assertEqual(self.module_Wikipedia.lookup(with_song_table, tracks_filename), True)
            self.assertEqual(self.module_Wikipedia.lookup(without_song_table, tracks_filename), None)
            #self.assertRaises(HTTPError, self.module_Wikipedia.lookup(with_404, tracks_filename))


if __name__ == '__main__':
    unittest.main()

