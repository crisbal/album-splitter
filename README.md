# Album-Splitter

Do you have a music album as a single file (locally or on YouTube), with all its tracks joined together? Do you want to split that album in its single tracks? Do you want to tag these tracks so your music player can get all the required infos from them?  

This script is for you!

## How to install

0. Install `ffmpeg` 
1. Install ```Python 3```
2. Install ```pip3```
3. Install ```virtualenv```
4. Fork/Clone/Download this repository
5. ```virtualenv -p /usr/bin/python3 venv``` (optional)
    * ```source venv/bin/activate```
6. Install the required packages via pip
    * ```pip install -r requirements.txt```


## Quick guide (from a local album)

1. Open tracks.txt
2. Add tracks info in this format:
    * ```<start-time> - <title>```
    * A track on each line
    * See *Examples* section
3. Run the script
    * Basic usage: ```python split.py -mp3 <path/to/your/album.mp3>```
    * More in the *Examples* section
4. Wait for the splitting process to complete
5. ????
6. You will find yout tracks in the "splits" folder 

## Quick guide (from a YouTube video)

1. Copy the YouTube URL of the album you want to download and split 
2. Find in the YouTube comments the tracklist with start-time and title
3. Open tracks.txt
4. Copy the tracklist in the file, adjusting for the supported format
    * ```<start-time> - <title>```
    * A track on each line 
5. Run the script
    * Basic usage: ```python split.py -yt <youtube_url>```
    * More in the *Examples* section
4. Wait for the Download and for the conversion
5. Wait for the splitting process to complete
5. ????
6. You will find yout tracks in the "splits" folder 

## Examples

### Downloading and splitting an album from YouTube
1. This is the album I want to download and split: https://www.youtube.com/watch?v=p_uqD4ng9hw
2. I find the tracklist in the comments and I copy that in tracks.txt, adjust it to my format
``` 
00:06 - When I Was Young
...
14:48 - Pretty Little Girl
<start-time> - <title> <--- remove this, just as a reminder of the format
```

3. I execute ``` python split.py -yt https://www.youtube.com/watch?v=p_uqD4ng9hw``` and wait
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
3. I execute ```python splits.py -mp3 DogsEatingDogsAlbum.mp3 --album "Dogs Eating Gods" --artist "blink-182" --folder "2012 - Dogs Eating Dogs"```
4. The program will execute, it will split the album, and mp3-tag each track with the author and  the album name I passed as a parameter (as well as track number and name). It will also put the files in the folder passed as an argument (instead of putting them in the default ```splits``` folder)

### Downloading and splitting an album from YouTube using a tracklist pulled from Wikipedia
1. This is the album I want to download and split: https://www.youtube.com/watch?v=p_uqD4ng9hw
2. This is the Wikipedia page that has the album tracklist: https://en.wikipedia.org/wiki/Dogs\_Eating\_Dogs
3. I execute ``` python split.py -yt https://www.youtube.com/watch?v=p_uqD4ng9hw -w https://en.wikipedia.org/wiki/Dogs\_Eating\_Dogs``` and wait
4. Once the process is complete I open ```splits``` and I find all my songs:
```
    When I Was Young.mp3 
    ...
    Pretty Little Girl.mp3
```
These songs are already mp3-tagged with their track name and track number, but not their author or their album, since we have not specified it.

The same works for the ```-amz``` (```--amazon```) parameter, instead you have to provide a link to Amazon.

### Show an help page for the script
``` python split.py -h ```

### Change the format for the tracks.txt file
1. Open split.py
2. Find this line ```regex = re.compile("(?P<start>.+)\s*\-\s*(?P<title>.+)")``` 
3. Change this line to whatever Regex you want but be sure to match at least ```(?P<start>.+)``` and ```(?P<title>.+)```
4. Test your changes
5. Have fun!

## TODO
Check the ```Issues``` page

## Need help?

If you need any help just create an Issue or send me an email at the address you can find on my profile.

## Want to help?

If you want to improve the code and submit a pull request feel free to do so.


## Licensce

GPL v3


