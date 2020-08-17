import re

DASHES = [' - ', ' ‑ ', ' ‒ ', ' – ', ' — ', ' ― ', ' − ', ' ﹘ ', ' ﹣ ', ' － ']
NDASHES = ['^{}'.format(_.strip()) for _ in DASHES]
EXPR_DASHES = ['(?:-)?[0-9]{1,3}' + _ for _ in DASHES]

NOISE = DASHES + NDASHES + EXPR_DASHES + ['(?:-)?[0-9]{1,3}\.']

# NOISE = [
#     ' - ', ' ‑ ', ' ‒ ', ' – ', ' — ', ' ― ', ' − ', ' ﹘ '
#     '^-',
#     '(?:-)?[0-9]{1,3} - ',
#     '(?:-)?[0-9]{1,3}\.'
# ]


def track_parser(s):
    """
    Matches any combination of the following:
    Beginning of a line:
        - 1. to 999.
        - 1 to 999
        - title
        - time in HH(optional):MM(required):SS(required) format
    Middle:
        - dash between spaces (' - ') separating the title and the time
    End of the line:
        - title
        - time in HH(optional):MM(required):SS(required) format

    Achieves the split by assuming as noise, every regex in the NOISE list.
    :param s: Track string to split
    :return: (time, title) tuple
    """

    # Making sure the encoding is UTF-8
    bs = bytes(s, 'utf-8')
    s = bs.decode('utf-8')

    # Knock out or ignore comments. - Redaundant
    if s[0] == '#':
        return 'comment', 'comment'

    try:
        # Explanation:                     HH optional          MM   and   SS required
        regex = re.compile('(?P<start>(?:([01]?\d|2[0-3]):)?([0-5]?\d):([0-5]?\d))')
        start_time = regex.search(s).group('start')
        title = re.sub('|'.join(NOISE), '', regex.sub('', s, count=1)).strip()
        return start_time, title
    except AttributeError:
        print('Error occurred when parsing the string: {}'.format(s))
        return '', ''
