# tvleg
tvleg: automatic subtitle downloader for http://legendas.tv.

This project was outdated and in Code Google so I added here to mantain and make improvemets.

## DESCRIPTION
Command line program, built in Python to download automatically or iterativelly subtitles from http://legendas.tv.

Has the ability to transverse a directory searching for media files or search subtitles for a single media file.

Initial tag tested on Ubuntu 14.04 only.
All following development tested in MAC OS 10.11 with Python 2.7.

## REQUIREMENTS
You have to have Python and some dependences installed.
1. Install [Homebrew](https://github.com/Homebrew/homebrew) to install all dependencies.
2. Install pip
3. Install unrar `brew install unrar`

## INSTALL
To install, just
```
git clone https://github.com/viniciusbig/tvleg.git
```
To see instructions of how to use, type:

```
python tvleg.py --help
```

## CONFIGURATION
Before you start, open the file ```data/config.json``` and add your [legendas.tv](http://legendas.tv) credentials.

## EXAMPLES
```
python tvleg.py --file some_file.mkv
```
Results: search subtitles to some_file.mkv
```
python tvleg.py --dir some_dir/
```
Results: search, recursevely, for movies/episodes in the informed directory. After that, start to search substitles to each movie or episode found.
```
python tvleg.py --dir some_dir/ --ignore
```
Results: same as above, but if a file found already has a subtitle, tvleg will ignore it.
```
python tvleg.py --dir some_dir/ --ignore --automatic
```
Results: same as above, but tvleg will not ask questions. Will try his best to download the best match for the files found.

## CHANGELOG
  - 11/28/2014 - Included authentication routine for legendas.tv. The site start (again) to ask for credentials to authorize downloads.
  - Code automatically imported Github from code.google.com/p/tvleg
  - 01/19/2016 - Updating decompress files process. Removing ```pyunpack```and using ```patool```instead.
  - 01/20/2016 - Organizing github branches with GitFlow. Development is now on ```develop```branch.
  - 01/21/2016 - Updating authentication routine to check whether logged in or not correctly. Creating new tag.
  - 02/09/2016 - Moving credentials to a config file. Removing username and password arguments.

## Todos

 - Check the best option to extract rar files on Mac OS.
 - Check why ```pyunpack```wasn`t work on Mac OS

License
----

MIT

**Free Software, Hell Yeah!**
