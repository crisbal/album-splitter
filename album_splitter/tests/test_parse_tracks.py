from album_splitter.parse_tracks import parse_line

import pytest


@pytest.mark.parametrize(
    ["input", "expected"],
    [
        ["01:23 Hello World", ("01:23", "Hello World")],
        ["Hello World 01:23:45", ("01:23:45", "Hello World")],
        ["Hello World", ValueError],
        ["Hello 11:22 World", ValueError],
        ["Hello World - 11:22", ("11:22", "Hello World")],
        ["Hello World    11:22", ("11:22", "Hello World")],
        ["11:22 - Hello World", ("11:22", "Hello World")],
        ["11:22 99 Red Baloons", ("11:22", "99 Red Baloons")],
        ["$P&C!AL'' 01:23:45", ("01:23:45", "$P&C!AL''")],
        ["$P&C!AL'' ろみチ 01:23:45", ("01:23:45", "$P&C!AL'' ろみチ")],
        # Underisable but we accept it for now
        ["01. 99 Red Baloons 11:22", ("11:22", "01. 99 Red Baloons")],
    ],
)
def test_parse_line(input, expected):
    if expected == ValueError:
        with pytest.raises(ValueError):
            parse_line(input)
    else:
        assert parse_line(input) == expected
