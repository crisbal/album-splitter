CC=pyinstaller
INST_DIR=/usr/local/bin/
DEPS=split.py split.spec split_init.py

dist/split: $(DEPS)
	$(CC) ./split.spec

install: dist/split
	rsync -av ./dist/split $(INST_DIR)

all: dist/split

clean:
	/bin/bash ./clean.sh