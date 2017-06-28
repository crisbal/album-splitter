import os
import sys

# ============================
#       General setup
# ============================
METADATA_PROVIDERS = []
for provider in os.listdir("MetaDataProviders"):
    if provider == "__init__.py" or provider[-3:] != ".py":
        continue
    METADATA_PROVIDERS.append(__import__("MetaDataProviders." + provider[:-3], fromlist=[""]))


# =============================
#   Youtube_dl configuration
# =============================
class YdlLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def ydl_hook(d):
    if d['status'] == 'downloading':
        sys.stdout.write('\r\033[K')
        sys.stdout.write('\tDownloading video | ETA: {} seconds'.format(str(d["eta"])))
        sys.stdout.flush()
    elif d['status'] == 'finished':
        sys.stdout.write('\r\033[K')
        sys.stdout.write('\tDownload complete\n\tConverting video to mp3')
        sys.stdout.flush()


ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '0',
    }],
    'logger': YdlLogger(),
    'progress_hooks': [ydl_hook],
}
