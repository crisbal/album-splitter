#################################
# A simple tracklist editor interface written with PyQt5
# --> Some python distributions claim that Tkinter is depricated!
# So, had to do it!
# PyQt5 code adopted from
#  https://www.learnpyqt.com/examples/no2pads-simple-notepad-clone/
#################################

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

import os
import sys
import io

class tracks_editor(QMainWindow):

    def __init__(self, trk_fname='tracks.txt', *args, **kwargs):
        super(tracks_editor, self).__init__(*args, **kwargs)

        init_win_size = [600, 700]
        self.resize(init_win_size[0], init_win_size[1])

        layout = QVBoxLayout()
        self.editor = QPlainTextEdit()

        # Setup the QTextEdit editor configuration
        # Checking it out from QT font database didn't work on
        # OS X. So, I've taken some brutal(?) approach by
        # selecting fonts myself.
        fixedfont = QFont("Consolas,Courier,monospace")
        fixedfont.setStyleHint(QFont.Monospace)

        fixedfont.setPointSize(12)
        self.editor.setFont(fixedfont)

        trk_f_path = os.path.realpath(trk_fname)
        # if not os.path.isfile(trk_f_path):
        #     with open(trk_f_path, 'w') as fp:
        #         fp.write('')
        self.path = trk_f_path
        if os.path.isfile(self.path):
            with open(self.path, 'rU') as fp:
                text = fp.read()
            self.editor.setPlainText(text)

        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # File Menu
        open_file_action = QAction("Open File...", self)
        open_file_action.triggered.connect(self.file_open)
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(open_file_action)

        save_file_action = QAction("Save", self)
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)

        saveas_file_action = QAction("Save As...", self)
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)

        print_action = QAction("Print...", self)
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_save)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_action = QAction("Select All", self)
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)
        edit_menu.addSeparator()

        wrap_action = QAction("Wrap text to Window", self)
        wrap_action.setCheckable(True)
        wrap_action.setCheckable(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        self.update_title()
        self.show()


    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Text documents (*.txt);All files (*.*)")

        if path:
            try:
                with io.open(path, 'r', encoding='utf8') as f:
                    text = f.read()

            except Exception as e:
                self.dialog_critical(str(e))

            else:
                self.path = path
                self.editor.setPlainText(text)
                self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        self._save_to_path(self.path)

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Text documents (*.txt);All files (*.*)")

        if not path:
            # If dialog is cancelled, will return ''
            return

        self._save_to_path(path)

    def exit_save(self):
        if self.path is None:
            return self.file_saveas()

        self._save_to_path(self.path)
        self.close()

    def closeEvent(self, event):
        self.exit_save()
        self.close()

    def _save_to_path(self, path):
        text = self.editor.toPlainText().encode("utf-8").decode('utf-8')
        try:
            with io.open(path, 'w', encoding='utf8') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle("%s - split.py Tracks Editor" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode( 1 if self.editor.lineWrapMode() == 0 else 0 )
