import os
import sys
import pkgutil

# ============================
#       General setup
# ============================
import MetaDataProviders

METADATA_PROVIDERS = [n for _, n, _ in pkgutil.iter_modules(['MetaDataProviders'])]

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
        sys.stdout.write('\tDownload complete\n\tConverting video to music file...')
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
