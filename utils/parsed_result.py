# A simple GUI implementation to show parsed results.

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

from .tracks_parser import tracks_parser_embed


def time_convert(seconds):
    seconds = float(seconds) / 1000
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)


class ParsedResult(QDialog):
    def __init__(self, parent=None, text='', duration=False):
        QDialog.__init__(self, parent)

        self.parent = parent
        self.text = text
        self.duration = duration
        self.dry_run = False

        self.tracks_start, self.tracks_titles = \
            tracks_parser_embed(self.text, self.duration)
        self.tracks_start_hhmmss = [time_convert(_) for _ in self.tracks_start]
        # self.track_numbers = [str(_) for _ in range(1, len(self.tracks_start))]

        self.initUI()

    def initUI(self):
        init_win_size = [400, 500]
        self.resize(init_win_size[0], init_win_size[1])

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        row_count = len(self.tracks_start)
        # col_count = 3
        col_count = 2

        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)

        content_map = {
            0: self.tracks_titles,
            1: self.tracks_start_hhmmss,
            2: self.tracks_start,
        }

        for x in range(row_count):
            for y in range(col_count):
                str_item = content_map[y][x]
                self.table.setItem(x, y, QTableWidgetItem(str_item))

            if y >= 1 and x > 0:
                if int(content_map[2][x]) <= int(content_map[2][x - 1]):
                    self.table.item(x, y).setBackground(Qt.red)
                    self.table.item(x - 1, y).setBackground(Qt.red)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # self.table.doubleClicked.connect(self.on_click)

    # @pyqtSlot()
    # def on_click(self):
    #     print("\n")
