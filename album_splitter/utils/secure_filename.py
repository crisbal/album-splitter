import os
import re
import unicodedata


# Taken and adapted from https://github.com/pallets/werkzeug/blob/e6c908f36c68eff4ecc10c405d8c2512f27e65a0/src/werkzeug/utils.py#L432
def secure_filename(filename: str) -> str:
    r"""Pass it a filename and it will return a secure version of it. This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.
    >>> secure_filename("My cool movie.mov")
    'My cool movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename('i contain cool \xfcml\xe4uts.txt')
    'i contain cool umlauts.txt'
    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.
    """
    _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")
    filename = str(_filename_ascii_strip_re.sub("", filename)).strip("._")

    return filename
