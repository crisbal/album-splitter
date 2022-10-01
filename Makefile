CC=pyinstaller
PYOPT=PYTHONOPTIMIZE=1
INST_DIR=/usr/local/bin/
UTILS=./utils/__init__.py ./utils/ffmpeg_utils.py ./utils/parsed_result.py ./utils/time_to_seconds.py ./utils/tracks_editor.py ./utils/update_time_change.py ./utils/find.py ./utils/split_song.py ./utils/track_parser.py ./utils/tracks_parser.py ./utils/write_tracks_to_file.py
METADATA=./MetaDataProviders/Amazon.py ./MetaDataProviders/Wikipedia.py
DEPS=split.py split.spec split_init.py $(UTILS) $(METADATA)
OUTF_NAME=album-split

split: $(DEPS)
	$(PYOPT) $(CC) ./split.spec
	cp -vf ./dist/split ./$(OUTF_NAME)

install: $(OUTF_NAME)
	rsync -av ./$(OUTF_NAME) $(INST_DIR)

all: split

clean:
	. ./clean.sh
