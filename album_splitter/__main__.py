import argparse
import datetime
import re
import sys
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import List, Dict, Any, Optional

from yt_dlp import YoutubeDL

from .parse_tracks import parse_tracks, parse_time_string, Track
from .split_file import split_file
from .tag_file import tag_file
from .utils.secure_filename import secure_filename
from .utils.ytdl_interface import ydl_opts


def get_parser():
    parser = argparse.ArgumentParser(
        prog="album-splitter",
        description="Split a single-file mp3 Album into its tracks.",
    )

    # TODO: add credentials ?

    input_group = parser.add_argument_group("Input")
    input_file_group = input_group.add_mutually_exclusive_group(required=True)
    input_file_group.add_argument(
        "-f", "--file", help="The file you want to split.", dest="audio_file"
    )
    input_file_group.add_argument(
        "-yt",
        "--youtube",
        help="The YouTube video url you want to download and split.",
        dest="youtube_url",
    )

    input_group.add_argument(
        "-t",
        "--tracks",
        help="Specify the tracks file. (default: %(default)s)",
        default="tracks.txt",
    )
    input_group.add_argument(
        "-d",
        "--duration",
        action="store_true",
        help="Tracks file format is in duration mode, as opposed to timestamp mode. (default: %(default)s)",
        default=False,
    )
    input_group.add_argument(
        "-et",
        "--extract-track",
        action = "store_true",
        help="Try to extract the tracklist from the description of the YouTube video. "
             "If it fails, searches in the top comments.",
        default=False,
    )

    tracks_metadata_group = parser.add_argument_group("Tracks Metadata")
    tracks_metadata_group.add_argument(
        "-a",
        "--artist",
        help="The artist that the ouput will be tagged with. (default: %(default)s)",
        default=None,
    )
    tracks_metadata_group.add_argument(
        "-A",
        "--album",
        help="The album that the ouput will be tagged with. (default: %(default)s)",
        default=None,
    )
    tracks_metadata_group.add_argument(
        "-y",
        "--year",
        help="The year that the ouput will be tagged with. (default: %(default)s)",
        default=None,
    )
    tracks_metadata_group.add_argument(
        "-md",
        "--metadata",
        dest="extra_metadata",
        help="Extra tags for the output. `key=value` format. (default: %(default)s)",
        action="append",
    )
    tracks_metadata_group.add_argument(
        "-em",
        "--extract-metadata",
        action = "store_true",
        help="Extract metadata from the YouTube video. "
             "Name will be the title of the video, artist will be the uploader, "
             "album will be the title of the video, and year will be the upload date. "
             "Any of these can be overridden with their respective flags.",
        default=False,
    )

    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-o",
        "--output",
        help="Specify the base output folder. (default: splits/)",
        metavar="FOLDER",
        dest="folder",
        default=None,
    )
    output_group.add_argument(
        "--format",
        help="Output file format to use. (default: %(default)s)",
        default="wav",
    )

    other_group = parser.add_argument_group("Other")
    other_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't split the file, just output the tracks. (default: %(default)s)",
        default=False,
    )

    return parser


class AlbumSplitterError(Exception):
    pass


timestamp_regex = re.compile(r"((?:\d+:)?[0-5]?\d:[0-5]?\d)")

def infer_tracks_from_text(text: str) -> List[Track]:
    """
    Try to infer a tracklist from a non-formatted text.
    It assumes the timestamps are in [hh]:mm:ss format and come before the track name.
    The track name is everything after the timestamp until the next timestamp, cleaned up.

    :param text: The text to parse.

    :return: A list of tracks.
    """

    # timestamps
    timestamps = timestamp_regex.findall(text)

    # track names
    timestamps_end = [m.end() for m in timestamp_regex.finditer(text)]
    track_names = [re.match(".*", text[end:]).group(0) for end in timestamps_end]

    # clean up track names
    trailing_chars_regex = re.compile(r"^[\s|:\-_~)\]}>]+")
    leading_chars_regex = re.compile(r"[\s|:_(\[{<]+$")

    track_names = [trailing_chars_regex.sub("", track_name) for track_name in track_names]
    track_names = [leading_chars_regex.sub("", track_name) for track_name in track_names]

    # create tracks
    tracks = [
        Track(track_name, parse_time_string(timestamp))
        for track_name, timestamp in zip(track_names, timestamps)
    ]

    return tracks


def extract_tracks_from_youtube(youtube_url: str) -> List[Track]:
    extractor_args = {
        "youtube": {
            "max_comments": ["10", "all", "0", "0"],    # up to 10 comments with no replies
            "comment_sort": "top"                       # sort by top comments
        }
    }

    # TODO: reduce payload size. We only need the chapters, description, and comments.
    with YoutubeDL({**ydl_opts, "getcomments": True, "extractor_args": extractor_args}) as ydl:
        info: Dict[str, Any] = ydl.extract_info(youtube_url, download = False)

        tracklist = info.get("chapters")

        # tracklist found in info, parse it
        if tracklist is not None:
            # TODO: remove "<Untitled chapter ...>" tracks ?
            return [Track(track["title"], parse_time_string(track["start_time"])) for track in tracklist]

        # tracklist not found in info, try to extract from description
        description = info.get("description")
        # TODO: put a min threshold on the number of timestamps ?
        if description is not None and 0 < len(timestamp_regex.findall(description)):
            return infer_tracks_from_text(description)

        # tracklist not found in description, try to extract from comments (max 10 comments)
        comments = info.get("comments")
        if comments is not None and 0 < len(comments):
            # we look for the comment with the most mm:ss timestamps
            timestamp_regex_matches = [timestamp_regex.findall(comment) for comment in comments]
            timestamp_regex_matches_len = [len(m) for m in timestamp_regex_matches]
            max_timestamp_regex_matches_len = max(timestamp_regex_matches_len)

            # TODO: put a min threshold on the number of timestamps ?
            if 0 < max_timestamp_regex_matches_len:
                max_timestamps_index = timestamp_regex_matches_len.index(max_timestamp_regex_matches_len)
                max_timestamps_comment = comments[max_timestamps_index]

                return infer_tracks_from_text(max_timestamps_comment)

        # tracklist not found in info, description, or comments, abort
        raise AlbumSplitterError(f"Tracklist not found in {youtube_url}")


def main(argv: Optional[List[str]] = None):
    parser = get_parser()
    args = parser.parse_args(argv)

    yt_video_id = None
    yt_video_name = None

    ydl_opts["postprocessors"][0]["preferredcodec"] = args.format

    if args.youtube_url:
        url_data = urlparse(args.youtube_url)
        if url_data.scheme == "":
            raise ValueError(f"Scheme (http, https) missing from provided URL")

        if (url_data.hostname or "").endswith("youtube.com"):
            query = parse_qs(url_data.query)
            yt_video_id = query["v"][0]
        elif (url_data.hostname or "").endswith("youtu.be"):
            yt_video_id = url_data.path.replace("/", "")
        else:
            raise ValueError(
                f"Unknown YouTube url {args.youtube_url}. (Supported youtube.com, youtu.be)"
            )

        if args.extract_metadata:
            # TODO: reduce payload size. We only need the uploader, title, and upload date
            with YoutubeDL(ydl_opts) as ydl:
                info: Dict[str, Any] = ydl.extract_info(args.youtube_url, download = False)

                yt_video_name = info.get("title")  # or "fulltitle" ?
                args.artist = args.artist or info.get("uploader")
                args.album = args.album or info.get("title")
                args.year = args.year or info.get("upload_date", "0000")[:4]

                # TODO: extract 'thumbnail' or biggest 'thumbnails' for image ?
        else:
            yt_video_name = yt_video_id


    # infer default output folder
    if not args.folder:
        if args.album or args.artist:
            args.folder = args.album or args.artist
            if args.album and args.artist:
                args.folder = secure_filename(f"{args.artist} - {args.album}")
        else:
            if args.youtube_url:
                assert yt_video_name
                args.folder = "./splits/{}".format(secure_filename(yt_video_name))
            else:
                args.folder = "./splits/{}".format(secure_filename(args.audio_file))

    print("Reading tracks")
    if args.extract_track:
        if not args.youtube_url:
            raise ValueError("Extracting tracks is only supported for YouTube videos.")

        tracks = extract_tracks_from_youtube(args.youtube_url)
    else:
        tracks_file = Path(args.tracks)
        if not tracks_file.exists():
            raise AlbumSplitterError(f"Can't find tracks file: {tracks_file}")

        tracks_content = tracks_file.read_text(encoding="utf-8", errors="ignore")
        tracks = parse_tracks(tracks_content, duration=args.duration)
        if not len(tracks):
            raise AlbumSplitterError("No tracks could be read/parsed from the tracks file.")

    # build the id3-tags
    tag_data = {}
    tag_data.update(
        {
            "artist": args.artist,
            "album": args.album,
            "year": args.year,
        }
    )

    for tag_data_line in args.extra_metadata or []:
        k, v = tag_data_line.split("=")
        tag_data[k] = v.replace('"', "").replace("'", "")

    if args.dry_run:
        for track in tracks:
            fmt_timestamp = datetime.timedelta(seconds=track.start_timestamp)
            print(f"{track.title} - {fmt_timestamp}")

        for k, v in tag_data.items():
            print(f"{k} - {v}")

        return
    else:
        print("Found the following tracks: ")
        for track in tracks:
            fmt_timestamp = datetime.timedelta(seconds=track.start_timestamp)
            print(f"\t{track.title} - {fmt_timestamp}")

    input_file = None
    if args.audio_file:
        input_file = Path(args.audio_file)
    elif args.youtube_url:
        assert yt_video_id

        # TODO: do the checks on the webm directly, then convert to format ? Would allow for multiple formats
        #       without having to download the video multiple times

        # youtube videos are downloaded as webm, so it makes no sense to use them as wav (10x bigger)
        input_file = Path(yt_video_id + f".{args.format}")
        if not input_file.exists():
            print("Downloading video from YouTube")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([args.youtube_url])

            print("\nConversion complete")
        else:
            print("Found matching file locally, no need to redownload from YouTube")

    if not input_file or not input_file.exists():
        raise AlbumSplitterError(f"Can't find input file: {input_file}")

    # create output folder
    outfolder = Path(args.folder)
    outfolder.mkdir(parents=True, exist_ok=True)

    # do the work
    print("Splitting into files... (this could take a while)")
    output_files = split_file(
        input_file, tracks, outfolder, output_format=str(input_file).split(".")[-1]
    )
    print("Tagging files, almost done...")
    for index, file in enumerate(output_files):
        track = tracks[index]
        tag_data.update({"title": str(track.title), "tracknumber": index + 1})
        tag_file(file, tag_data)

    print(f"Done! You can find your tracks in {outfolder}")


def playlist_dispatch():
    """
    Detect if the URL is a playlist, and if we have tracklist extraction enabled.
    If so, this will call main() for each video in the playlist, extracting the tracks for each.
    """

    parser = get_parser()
    args = parser.parse_args()

    if args.youtube_url and args.extract_track:
        # TODO: reduce payload size. We only need the urls, not the full info
        with YoutubeDL({**ydl_opts, "compat_opts": ["no-youtube-unavailable-videos"]}) as ydl:
            info: Dict[str, Any] = ydl.extract_info(args.youtube_url, download = False)

            if info.get("_type") == "playlist":
                entries = info.get("entries")

                if not entries:
                    raise AlbumSplitterError("No entry found in playlist")

                print(f"Playlist detected, {len(entries)} entries found")

                argv = sys.argv.copy()
                url_index = argv.index(args.youtube_url)

                for entry in entries:
                    try:
                        # substitute the URL in the argv list with the current entry
                        url = entry.get("webpage_url")
                        argv[url_index] = url

                        main(argv)
                    except AlbumSplitterError as e:
                        print("Error:", e, file = sys.stderr)

                    print("")

                sys.exit(0)

def main_entry():
    playlist_dispatch()

    try:
        main()
    except AlbumSplitterError as e:
        print("Error:", e, file = sys.stderr)
        sys.exit(-1)


if __name__ == "__main__":
    main_entry()
