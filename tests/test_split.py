#test_split.py
#run this command to test all: 'python3 -m unittest discover -s tests -v'

import unittest

from tests.resources import constants

if constants.UPDATE_HTML_FILES_CAPTURED:
    from tests.resources import html_file_downloader

class TestSplit(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        pass
        
    #def test_compare_compare(self):
    #    pass


if __name__ == '__main__':
    unittest.main()
