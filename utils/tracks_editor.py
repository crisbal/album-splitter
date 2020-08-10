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

class tracks_editor(QMainWindow):

    def __init__(self, trk_fname='tracks.txt', *args, **kwargs):
        super(tracks_editor, self).__init__(*args, **kwargs)

        layout = QVBoxLayout()
        self.editor = QPlainTextEdit()

        # Setup the QTextEdit editor configuration
        fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
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
                with open(path, 'rU') as f:
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

    def closeEvent(self, event):
        self.exit_save()
        self.close()

    def _save_to_path(self, path):
        text = self.editor.toPlainText()
        try:
            with open(path, 'w') as f:
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

# import tkinter as tk
# from tkinter.filedialog import askopenfilename, asksaveasfilename
# import os
#
# class tracks_editor(object):
#     def __init__(self, trk_fname='tracks.txt', trk_info=''):
#         self.trk_fname = trk_fname
#         self.trk_info = trk_info
#         if os.path.isfile(self.trk_fname):
#             with open(self.trk_fname, 'r') as f:
#                 self.trk_info = f.read()
#
#         self.window_title = "Tracklist editor - {}".format(self.trk_fname)
#
#         self.main_window()
#
#     def main_window(self):
#         self.window = tk.Tk()
#         self.window.title(self.window_title)
#         self.window.rowconfigure(0, minsize=800, weight=1)
#         self.window.columnconfigure(1, minsize=800, weight=1)
#
#         self.txt_edit = tk.Text(self.window)
#         fr_buttons = tk.Frame(self.window, relief=tk.RAISED, bd=2)
#         btn_open = tk.Button(fr_buttons, text="Open", command=self.open_file)
#         btn_save = tk.Button(fr_buttons, text="Save As...", command=self.save_file)
#
#         btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
#         btn_save.grid(row=1, column=0, sticky="ew", padx=5)
#
#         fr_buttons.grid(row=0, column=0, sticky="ns")
#         self.txt_edit.grid(row=0, column=1, sticky="nsew")
#
#         self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
#         self.window.mainloop()
#
#     def open_file(self):
#         """Open a file for editing."""
#         filepath = askopenfilename(
#             filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
#         )
#         if not filepath:
#             return
#         txt_edit.delete(1.0, tk.END)
#         with open(filepath, "r") as input_file:
#             text = input_file.read()
#             self.txt_edit.insert(tk.END, text)
#         self.window.title("Tracklist editor - {}".format(filepath))
#
#     def save_file(self):
#         """Save the current file as a new file."""
#         filepath = asksaveasfilename(
#             defaultextension="txt",
#             filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
#         )
#         if not filepath:
#             return
#         with open(filepath, "w") as output_file:
#             text = self.txt_edit.get(1.0, tk.END)
#             output_file.write(text)
#         self.window.title("Tracklist editor - {}".format(filepath))
#
#     def on_closing(self):
#         with open(self.trk_fname, 'w') as output_file:
#             text = self.txt_edit.get(1.0, tk.END)
#             output_file.write(text)
#         self.window.destroy()
