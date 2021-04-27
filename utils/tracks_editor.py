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

from .find import Find
from .parsed_result import ParsedResult

import os
# import sys
import io

# Line number feature implementation
# adopted from ...
# https://stackoverflow.com/a/49790764
#

class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class QCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


class tracks_editor(QMainWindow):

    def __init__(self, trk_fname='tracks.txt', duration=False, *args, **kwargs):
        super(tracks_editor, self).__init__(*args, **kwargs)

        self.duration = duration
        init_win_size = [600, 700]
        self.resize(init_win_size[0], init_win_size[1])

        layout = QVBoxLayout()
        # self.editor = QPlainTextEdit()
        self.editor = QCodeEditor()

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
            with io.open(self.path, 'r', encoding='utf8') as fp:
                text = fp.read()
            self.editor.setPlainText(text)

        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # File Menu
        open_file_action = QAction("&Open File...", self)
        open_file_action.triggered.connect(self.file_open)
        open_file_shortcut = QShortcut(QKeySequence('Ctrl+O'), self)
        open_file_shortcut.activated.connect(self.file_open)
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(open_file_action)

        save_file_action = QAction("&Save", self)
        save_file_action.triggered.connect(self.file_save)
        save_file_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        save_file_shortcut.activated.connect(self.file_save)
        file_menu.addAction(save_file_action)

        saveas_file_action = QAction("Save &As...", self)
        saveas_file_action.triggered.connect(self.file_saveas)
        saveas_file_shortcut = QShortcut(QKeySequence('Ctrl+Shift+S'), self)
        saveas_file_shortcut.activated.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)

        print_action = QAction("&Print...", self)
        print_action.triggered.connect(self.file_print)
        print_shortcut = QShortcut(QKeySequence('Ctrl+P'), self)
        print_shortcut.activated.connect(self.file_print)
        file_menu.addAction(print_action)
        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.exit_save)
        exit_shortcut = QShortcut(QKeySequence('Ctrl+Q'), self)
        exit_shortcut.activated.connect(self.exit_save)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.triggered.connect(self.editor.undo)
        undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        undo_shortcut.activated.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.triggered.connect(self.editor.redo)
        redo_shortcut = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
        redo_shortcut.activated.connect(self.editor.redo)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.triggered.connect(self.editor.cut)
        cut_shortcut = QShortcut(QKeySequence('Ctrl+X'), self)
        cut_shortcut.activated.connect(self.editor.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.triggered.connect(self.editor.copy)
        copy_shortcut = QShortcut(QKeySequence('Ctrl+C'), self)
        copy_shortcut.activated.connect(self.editor.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.triggered.connect(self.editor.paste)
        paste_shortcut = QShortcut(QKeySequence('Ctrl+V'), self)
        paste_shortcut.activated.connect(self.editor.paste)
        edit_menu.addAction(paste_action)

        select_action = QAction("Select &All", self)
        select_action.triggered.connect(self.editor.selectAll)
        select_shortcut = QShortcut(QKeySequence('Ctrl+A'), self)
        select_shortcut.activated.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)
        edit_menu.addSeparator()

        find_action = QAction("&Find and Replace", self)
        find_action.triggered.connect(self.open_find_dialog)
        find_shortcut = QShortcut(QKeySequence('Ctrl+F'), self)
        find_shortcut.activated.connect(self.open_find_dialog)
        edit_menu.addAction(find_action)
        edit_menu.addSeparator()

        wrap_action = QAction("&Wrap text to Window", self)
        wrap_action.setCheckable(True)
        wrap_action.setCheckable(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        run_menu = self.menuBar().addMenu("&Run")

        parse_action = QAction("Pa&rse", self)
        parse_action.triggered.connect(self.run_parser)
        parse_shortcut = QShortcut(QKeySequence('F5'), self)
        parse_shortcut.activated.connect(self.run_parser)
        run_menu.addAction(parse_action)

        self.update_title()
        self.show()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open file", "", "Text documents (*.txt);All files (*.*)")

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
        path, _ = QFileDialog.getSaveFileName(
            self, "Save file", "", "Text documents (*.txt);All files (*.*)")

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
        self.setWindowTitle("%s - split.py Tracks Editor" %
                            (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(
            1 if self.editor.lineWrapMode() == 0 else 0)

    def open_find_dialog(self):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        fnd = Find(self, pre_selected_text=selected_text)
        fnd.show()

    def run_parser(self):
        text = self.editor.toPlainText().encode("utf-8").decode('utf-8')
        parsed = ParsedResult(self, text=text, duration=self.duration)
        parsed.show()
