# tvleg
Automatically exported from code.google.com/p/tvleg

tvleg: automatic subtitle downloader for legendas.tv

DESCRIPTION
Command line program, built in Python to download automatically or iterativelly subtitles from legendas.tv.

Has the ability to transverse a directory searching for media files or search subtitles for a single media file

Tested in Ubuntu 14.04 only.

INSTALL
To install, just

git clone https://fernando.nemec@code.google.com/p/tvleg/`

To see instructions of how to use, type:

python tvleg.py --help

EXAMPLES
python tvleg.py --username foo --password bar --file some_file.mkv

Results: search subtitles to some_file.mkv

python tvleg.py --username foo --password bar --dir some_dir/

Results: search, recursevely, for movies/episodes in the informed directory. After that, start to search substitles to each movie or episode found.

python tvleg.py --username foo --password bar --dir some_dir/ --ignore

Results: same as above, but if a file found already has a subtitle, tvleg will ignore it.

python tvleg.py --username foo --password bar --dir some_dir/ --ignore --automatic

Results: same as above, but tvleg will not ask questions. Will try his best to download the best match for the files found.

CHANGELOG
# 28/11/2014 - Included authentication routine for legendas.tv. The site start (again) to ask for credentials to authorize downloads.
