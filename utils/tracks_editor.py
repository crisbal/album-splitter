#################################
# A simple tracklist editor interface written with Tkinter
#################################

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import os

class tracks_editor(object):
    def __init__(self, trk_fname='tracks.txt', trk_info=''):
        self.trk_fname = trk_fname
        self.trk_info = trk_info
        if os.path.isfile(self.trk_fname):
            with open(self.trk_fname, 'r') as f:
                self.trk_info = f.read()

        self.window_title = "Tracklist editor - {}".format(self.trk_fname)

        self.main_window()

    def main_window(self):
        self.window = tk.Tk()
        self.window.title(self.window_title)
        self.window.rowconfigure(0, minsize=800, weight=1)
        self.window.columnconfigure(1, minsize=800, weight=1)

        self.txt_edit = tk.Text(self.window)
        fr_buttons = tk.Frame(self.window, relief=tk.RAISED, bd=2)
        btn_open = tk.Button(fr_buttons, text="Open", command=self.open_file)
        btn_save = tk.Button(fr_buttons, text="Save As...", command=self.save_file)

        btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        btn_save.grid(row=1, column=0, sticky="ew", padx=5)

        fr_buttons.grid(row=0, column=0, sticky="ns")
        self.txt_edit.grid(row=0, column=1, sticky="nsew")

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def open_file(self):
        """Open a file for editing."""
        filepath = askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        txt_edit.delete(1.0, tk.END)
        with open(filepath, "r") as input_file:
            text = input_file.read()
            self.txt_edit.insert(tk.END, text)
        self.window.title("Tracklist editor - {}".format(filepath))

    def save_file(self):
        """Save the current file as a new file."""
        filepath = asksaveasfilename(
            defaultextension="txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        with open(filepath, "w") as output_file:
            text = self.txt_edit.get(1.0, tk.END)
            output_file.write(text)
        self.window.title("Tracklist editor - {}".format(filepath))

    def on_closing(self):
        with open(self.trk_fname, 'w') as output_file:
            text = self.txt_edit.get(1.0, tk.END)
            output_file.write(text)
        self.window.destroy()
