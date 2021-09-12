import argparse
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import datetime

from .parse_tracks import parse_tracks
from .tag_file import tag_file
from .split_file import split_file
from .utils.secure_filename import secure_filename
from .utils.ytdl_interface import ydl_opts

from youtube_dl import YoutubeDL


def get_parser():
    parser = argparse.ArgumentParser(
        prog="album-splitter",
        description="Split a single-file mp3 Album into its tracks.",
    )

    input_group = parser.add_argument_group("Input")
    input_file_group = input_group.add_mutually_exclusive_group(required=True)
    input_file_group.add_argument("-f", "--file", help="The file you want to split.", dest="audio_file")
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

    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-o",
        "--output",
        help="Specify the base output folder. (default: splits/)",
        metavar="FOLDER",
        dest="folder",
        default=None,
    )

    other_group = parser.add_argument_group("Other")
    other_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't split the file, just output the tracks. (default: %(default)s)",
        default=False,
    )

    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    # infer default output folder
    if not args.folder:
        if args.album or args.artist:
            args.folder = args.album or args.artist
            if args.album and args.artist:
                args.folder = secure_filename(f"{args.artist} - {args.album}")
        else:
            if args.youtube_url:
                url_data = urlparse(args.youtube_url)
                query = parse_qs(url_data.query)
                video_id = query["v"][0]
                args.folder = "./splits/{}".format(secure_filename(video_id))
            else:
                args.folder = "./splits/{}".format(secure_filename(args.audio_file))

    print("Reading tracks file")
    tracks_file = Path(args.tracks)
    if not tracks_file.exists():
        print(f"Can't find tracks file: {tracks_file}")
        exit(-1)
    tracks_content = tracks_file.read_text(encoding="utf-8", errors="ignore")
    tracks = parse_tracks(tracks_content, duration=args.duration)
    if not len(tracks):
        print("No tracks could be read/parsed from the tracks file.")
        exit(-1)

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
        exit()
    else:
        print("Found the following tracks: ")
        for track in tracks:
            fmt_timestamp = datetime.timedelta(seconds=track.start_timestamp)
            print(f"\t{track.title} - {fmt_timestamp}")
    input_file = None
    if args.audio_file:
        input_file = Path(args.audio_file)
    elif args.youtube_url:
        url_data = urlparse(args.youtube_url)
        query = parse_qs(url_data.query)
        video_id = query["v"][0]
        input_file = Path(video_id + ".wav")
        if not input_file.exists():
            print("Downloading video from YouTube")
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([args.youtube_url])
            print("\nConversion complete")
        else:
            print("Found matching file locally, no need to redownload from YouTube")

    if not input_file or not input_file.exists():
        print(f"Can't find input file: {input_file}")
        exit(-1)

    # create output folder
    outfolder = Path(args.folder)
    outfolder.mkdir(parents=True, exist_ok=True)

    # do the work
    print("Splitting into files... (this could take a while)")
    output_files = split_file(input_file, tracks, outfolder, output_format=str(input_file).split(".")[-1])
    print("Tagging files, almost done...")
    for index, file in enumerate(output_files):
        track = tracks[index]
        tag_data.update({
            "title": str(track.title),
            "tracknumber": index + 1
        })
        tag_file(file, tag_data)
    print("Done!")
