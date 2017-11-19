# album-splitter

Do you have a music album as a single file (locally or on YouTube), with all its tracks joined together? Do you want to split that album in its single tracks? Do you want to tag these tracks so your music player can get all the required info from them?

This script is for you!

## How to install

0. Install `ffmpeg`
1. Install ```Python 3```
2. Install ```pip3```
3. Install ```virtualenv``` (optional)
4. Fork/Clone/Download this repository
5. ```virtualenv -p /usr/bin/python3 venv``` (optional)
    * ```source venv/bin/activate```
6. Install the required packages via pip
    * ```pip install -r requirements/prod.txt```

## Quick guide (from a local album)

1. Create a copy of the tracks.txt.example, rename it as tracks.txt and
   delete the lines starting with #.
2. Open tracks.txt
3. Add tracks info in this format:
    * ```<start-time> - <title>```
    * A track on each line
    * See *Examples* section, many other formats supported
4. Run the script
    * Basic usage: ```python split.py -mp3 <path/to/your/album.mp3>```
    * More in the *Examples* section
5. Wait for the splitting process to complete
6. You will find your tracks in the `splits` folder

## Quick guide (from a YouTube video)

1. Copy the YouTube URL of the album you want to download and split
2. Find in the YouTube comments the tracklist with start-time and title
3. Create a copy of the tracks.txt.example, rename it as tracks.txt and
   delete the lines starting with #.
4. Open tracks.txt
5. Copy the tracklist in the file, adjusting for the supported formats
    * ```<start-time> - <title>```
    * A track on each line
6. Run the script
    * Basic usage: ```python split.py -yt <youtube_url>```
    * More in the *Examples* section
7. Wait for the Download and for the conversion
8. Wait for the splitting process to complete
9. You will find your tracks in the `splits` folder

## Examples

### Downloading and splitting an album from YouTube

1. This is the album I want to download and split: `https://www.youtube.com/watch?v=p_uqD4ng9hw`
2. I find the tracklist in the comments and I copy that in `tracks.txt`, eventually adjusting it to a supported format for the tracklist
```
00:06 - When I Was Young
...
14:48 - Pretty Little Girl
<start-time> - <title> <--- remove this, just as a reminder of the format
```

3. I execute ```python split.py -yt "https://www.youtube.com/watch?v=p_uqD4ng9hw"``` and wait
4. Once the process is complete I open ```splits``` and I find all my songs:
```
    When I Was Young.mp3
    ...
    Pretty Little Girl.mp3
```
These songs are already mp3-tagged with their track name and track number, but not their author or their album, since we have not specified it.

### Splitting and tagging with Author and Album a local file

1. I somehow got the file ```DogsEatingDogsAlbum.mp3``` that I want to split
2. I set the tracklist in ```tracks.txt``` (same tracks as before)
3. I execute ```python split.py -mp3 DogsEatingDogsAlbum.mp3 --album "Dogs Eating Gods" --artist "blink-182" --folder "2012 - Dogs Eating Dogs"```
4. The program will execute, it will split the album, and mp3-tag each track with the author and  the album name I passed as a parameter (as well as track number and name). It will also put the files in the folder passed as an argument (instead of putting them in the default ```splits``` folder)

### Downloading and splitting an album from YouTube using a tracklist pulled from Wikipedia or Amazon

1. This is the album I want to download and split: https://www.youtube.com/watch?v=p_uqD4ng9hw
2. This is the Wikipedia page that has the album tracklist: https://en.wikipedia.org/wiki/Dogs\_Eating\_Dogs
3. I execute ```python split.py -yt "https://www.youtube.com/watch?v=p_uqD4ng9hw" --metadata "https://en.wikipedia.org/wiki/Dogs_Eating_Dogs"``` and wait
4. Once the process is complete I open ```splits``` and I find all my songs:
```
    When I Was Young.mp3
    ...
    Pretty Little Girl.mp3
```
These songs are already mp3-tagged with their track name and track number, but not their author or their album, since we have not specified it (specify them using the `--author` and `--album` flags).

The same thing works if you provide a link to the Amazon page for that album.

### Show an help page for the script

```python split.py -h```

## Supported formats for the track list (`tracks.txt`)

These are just some examples.

* [hh:]mm:ss - Title
* Title - [hh:]mm:ss
* Title [hh:]mm:ss
* TrackNumber. Title [hh:]mm:ss
* TrackNumber - Title [hh:]mm:ss

To see which data would be extracted from the tracklist use the option `--dry-run`. It also works if you pass any external `--metadata` url.

Example:

```
python split.py
    --dry-run
    -yt https://www.youtube.com/watch?v=T44T8JdMOak
    --metadata https://www.amazon.com/Enema-State-Blink-182/dp/B00000IPAX
```

will output

```
**** DRY RUN ****
Matched with a metadata provider...
Parsing tracks.txt
Dumpweed [Explicit] *** 00:00:00
...
Anthem *** 00:31:40
```


## TODO

Check the ```Issues``` page

## Need help?

If you need any help just create an Issue or send me an email at the address you can find on my profile.

## Want to help?

If you want to improve the code and submit a pull request feel free to do so.

## Licence

GPL v3


