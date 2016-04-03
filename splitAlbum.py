import easygui as eg
import subprocess
import os
import re

source = eg.buttonbox(msg="How would you like to get the album?", title="Album Splitter", choices=("Youtube", "File"))

if source == "File":
    link = "-mp3 \"" + os.path.abspath(eg.fileopenbox(msg="Select mp3 file", title="Album Splitter", default='*', filetypes="\*.mp3") + "\"")
else:
    link = "-yt \"" + eg.enterbox(msg="Enter Youtube link", title="Album Splitter", default="", strip=True, image=None, root=None) + "\""
    
format = eg.choicebox(msg="Select format", title="Album Splitter", choices=("<start time> - <title>", "<start time> <title>"))


tracks = eg.codebox(msg="Paste track list:", title="Album Splitter", text="")

if format == "<start time> - <title>":
    with open("tracks.txt", 'w') as t:
        t.write(tracks)
if format == "<start time> <title>":    
    tracks = tracks.split('\n')
    regex = re.compile("(\d*\s\-\s)*(?P<start>\S+)\s*(?P<title>.+)")
    for i in range(len(tracks)):
        if tracks[i] != "":
            m = regex.match(tracks[i])
            tStart = m.group('start').strip()
            tTitle = m.group('title').strip()
            tracks[i] = tStart + " - " + tTitle
    with open("tracks.txt", "w") as t:
        t.write("\n".join(tracks))

try:
    cmd = "python split.py " + link
    print(cmd)
    out = os.system(cmd)
    #print(out)
    #subprocess.call(("python split.py " + link))
    #out_str = subprocess.check_output(cmd, shell=True)
    #subprocess.Popen(cmd, shell=True)

except:
    eg.exceptionbox(msg="Album Splitter has crashed", title="Album Splitter")
