#!/usr/bin/env python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from utils import (split_song, time_to_seconds,
                   track_parser, update_time_change,
                   tracks_editor)

import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("testGUI")
    window = tracks_editor(trk_fname='tracks.txt')
    app.exec_()
