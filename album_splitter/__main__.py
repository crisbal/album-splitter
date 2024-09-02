import argparse
import datetime
import sys
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import List, Dict, Any, Optional

from yt_dlp import YoutubeDL

from .parse_tracks import parse_tracks, infer_tracks_from_text, timestamp_regex, Track
from .split_file import split_file
from .tag_file import tag_file
from .utils.secure_filename import secure_filename_simple
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


def extract_tracks_from_youtube(youtube_url: str) -> List[Track]:
    extractor_args = {
        "youtube": {
            "comment_sort": ["top"],                     # sort by top comments
            "max_comments": ["all", "all", "0", "0"],    # up to 10 comments with no replies
        }
    }

    with YoutubeDL({**ydl_opts, "getcomments": True, "extractor_args": extractor_args}) as ydl:
        info: Dict[str, Any] = ydl.extract_info(youtube_url, download = False)

        # NOTE: chapters are disabled as they are unreliable in numerous cases (number, names, etc.)
        # tracklist = info.get("chapters")

        # tracklist not found in info, try to extract from description
        description = info.get("description")
        size_tracks_in_description = len(timestamp_regex.findall(description)) if description is not None else 0
        if 2 < size_tracks_in_description:
            return infer_tracks_from_text(description)

        # tracklist not found in description, try to extract from comments (max 10 comments)
        comment_entries = info.get("comments")
        if comment_entries is not None and 0 < len(comment_entries):
            comments = [entry["text"] for entry in comment_entries[:10]]

            # we look for the comment with the most mm:ss timestamps
            timestamp_regex_matches = [timestamp_regex.findall(comment) for comment in comments]
            timestamp_regex_matches_len = [len(m) for m in timestamp_regex_matches]
            max_timestamp_regex_matches_len = max(timestamp_regex_matches_len)

            if 2 < max_timestamp_regex_matches_len:
                max_timestamps_index = timestamp_regex_matches_len.index(max_timestamp_regex_matches_len)
                max_timestamps_comment = comments[max_timestamps_index]

                return infer_tracks_from_text(max_timestamps_comment)

        # tracklist not found in info, description, or comments, abort
        if info.get("title") is None:
            raise AlbumSplitterError(f"Tracklist not found in {youtube_url}")
        else:
            raise AlbumSplitterError(f"Tracklist not found in {youtube_url} ({info['title']})")


def main(argv: Optional[List[str]] = None):
    parser = get_parser()
    args = parser.parse_args(argv)

    yt_video_id = None
    yt_thumbnails = []

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
            with YoutubeDL(ydl_opts) as ydl:
                info: Dict[str, Any] = ydl.extract_info(args.youtube_url, download = False)

                args.folder = info.get("title").strip()  # or "fulltitle" ?
                args.artist = args.artist or info.get("uploader").strip()
                args.album = args.album or info.get("title").strip()
                args.year = args.year or info.get("upload_date", "0000")[:4]

                # TODO: get thumbnail for all chapters (complicated without downloading the video
                #       if chapters are not there)
                # I think we can get the thumbnail for each chapter if chapters are there
                if info.get("thumbnail"):
                    yt_thumbnails = [info.get("thumbnail")]

    # infer default output folder
    if not args.folder:
        if args.album or args.artist:
            args.folder = args.album or args.artist
            if args.album and args.artist:
                args.folder = f"{args.artist} - {args.album}"
        else:
            if args.youtube_url:
                assert yt_video_id
                args.folder = "./splits/{}".format(yt_video_id)
            else:
                args.folder = "./splits/{}".format(args.audio_file)

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

    # sort tracks by start timestamp (in case they are not already), as ffmpeg requires them to be
    sorted_tracks = sorted(tracks, key = lambda t: t.start_timestamp)
    if sorted_tracks != tracks:
        print("Warning: Tracks were not in the right order. Check the source for mistakes.")
    tracks = sorted_tracks

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
        input_file = Path(f"{yt_video_id}.{args.format}")
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
    outfolder = Path(secure_filename_simple(args.folder))
    outfolder.mkdir(parents=True, exist_ok=True)

    # TODO: try to get refine the timestamps by detecting the silence between tracks (+- 3 seconds)
    #       it would help correct inaccuracies and allow for a more precise split (0.5s off can be jarring)

    # do the work
    print("Splitting into files... (this could take a while)")
    output_files = split_file(
        input_file, tracks, outfolder, output_format=str(input_file).split(".")[-1]
    )

    print("Tagging files, almost done...")
    # download thumbnails
    yt_thumbnails_paths = [outfolder / f"thumbnail_{index}.jpg" for index, _ in enumerate(yt_thumbnails)]
    for thumbnail_url, thumbnail_file in zip(yt_thumbnails, yt_thumbnails_paths):
        if not thumbnail_file.exists():
            urllib.request.urlretrieve(thumbnail_url, thumbnail_file)

    # extend the thumbnails to the length of the tracks if needed
    if len(yt_thumbnails_paths) == 1:
        yt_thumbnails_paths *= len(tracks)

    for index, file in enumerate(output_files):
        track = tracks[index]
        tag_data.update({
            "title": str(track.title),
            "tracknumber": index + 1,
            "totaltracks": len(tracks),
        })

        if index < len(yt_thumbnails_paths):
            tag_data["artwork"] = yt_thumbnails_paths[index].read_bytes()

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
        with YoutubeDL({**ydl_opts, "extract_flat": True, "compat_opts": ["no-youtube-unavailable-videos"]}) as ydl:
            info: Dict[str, Any] = ydl.extract_info(args.youtube_url, download = False)
            if info.get("_type") == "playlist":
                entries = info.get("entries")

                if not entries:
                    raise AlbumSplitterError("No entry found in playlist")

                print(f"Playlist detected, {len(entries)} entries found")

                argv = sys.argv[1:]
                url_index = argv.index(args.youtube_url)

                for entry in entries:
                    try:
                        # substitute the URL in the argv list with the current entry
                        url = entry.get("url")
                        argv[url_index] = url

                        main(argv)
                    except AlbumSplitterError as e:
                        print("Error:", e, file = sys.stderr)

                    print("")

                sys.exit(0)

def main_entry():
    try:
        playlist_dispatch()
        main()
    except AlbumSplitterError as e:
        print("Error:", e, file = sys.stderr)
        sys.exit(-1)


if __name__ == "__main__":
    main_entry()
