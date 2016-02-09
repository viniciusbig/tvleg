#!/usr/bin/python

import signal
import sys
import mechanize
import cookielib
import os
import re
import pickle
import urllib
import argparse
# from pyunpack import Archive
import patoolib
import json

# Mechanize Tutorial
# http://stockrt.github.io/p/emulating-a-browser-in-python-with-mechanize/
# http://wwwsearch.sourceforge.net/mechanize/

class FileFinder:
	def __init__(self, dir, application = None):
		self.extensions = ("avi","mkv","mp4")

		if not os.path.exists(dir):
			if not application.args.quiet: print dir + " doesn't exist."
			return

		if not os.access(dir, os.R_OK):
			if not application.args.quiet: print dir + " isn't readable."
			return

		if not application.args.quiet: print "Filtering files by these extensions: " + ", ".join(self.extensions)

		self.files = []
		for root, dirs, files in os.walk(dir):
			for file in files:
				if file.endswith(self.extensions):
					f = os.path.join(root , file)
					( base , ext ) = os.path.splitext(f)
					if application.args.ignore and os.path.exists(base + ".srt"):
						if not application.args.quiet: print "Ignoring " + f + ". Subtitle found."
						continue
					self.files.append(f)

class File2Query:
	def __init__(self):
		self.original = None
		self.series = None
		self.episode = None
		self.release = None
		self.year = None
		self.valid = False
		self.as_file = True

		delim = "[\.| |-|\(|\[|\{|\}|\]|\)]"
		self.patterns = {
			"(.+?)s([0-9][0-9])e([0-9][0-9])(.*?)$":("tv",4),
			"(.+?)" + delim + "([1-2][0|9][0-9][0-9])"+ delim +"(.*?)$":("movie",3),
			"(.+?)\.([0-9])([0-9][0-9])\.(.*?)$":("tv",4),
		}

	def parse(self, file):

		self.original = file

		for pattern in self.patterns.keys():
			type, fields = self.patterns[pattern]

			if self.as_file:
				result = re.match(pattern, os.path.splitext(os.path.basename(file))[0], re.I)
			else:
				result = re.match(pattern, file, re.I)

			if result and result.lastindex == fields:
				if type == "tv":
					self.valid = True
					self.series = re.sub("[^0-9a-z ]", "", self.normalizeName(result.group(1)), 0, re.I).lower()
					self.release = result.group(4)
					season = result.group(2).strip().lower()
					chapter = result.group(3).strip().lower()
					self.episode = "s" + "%02d" % int(season) + "e" + "%02d" % int(chapter)

					result = re.match(".*[\.\-]([0-9a-z]+)", self.release, re.I)
					if result:
						self.release = result.group(1)

					self.release = re.sub("[^0-9a-z ]", "", self.normalizeName(self.release), 0, re.I).lower()

				if type == "movie":
					self.series = re.sub("[^0-9a-z ]", "", self.normalizeName(result.group(1)), 0, re.I).lower()
					self.episode = result.group(2)
					self.release = self.normalizeName(result.group(3))
					self.valid = True

			if self.valid:
				break

		if not self.valid:
			parent = os.path.basename(os.path.dirname(file))
			if len(parent) > 0:
				self.as_file = False
				self.parse(parent)
				self.as_file = True
				self.original = file

	def normalizeName(self, name):
		name = re.sub("[\.\-]", " ", name, 0 , re.I)	# dots to spaces
		name = re.sub("\s+", " ", name, 0 , re.I)		# multi spaces to single spaces
		name = re.sub("\[.*?\]", "", name, 0 , re.I)	# remove comments in brackets. Ex: [rargb]
		# remove common words that doesn't change the search query whatsoever
		name = re.sub("(webrip|hddvd|dvd9|dualaudio|5 1ch|dvdrip|unrated|dd[2-7] 1|ac3|imax|edition|DTS|dxva|limited|brrip|xvid|480p|720p|1080p|web dl|x\ ?264|hdtv|aac2 0|bluray|h\ ?264|bdrip)", "", name, 0 , re.I)
		name = re.sub("\s+", " ", name, 0 , re.I) 		# multi spaces to single spaces
		name = name.strip()
		return name

	def dump(self):
		print "-------------------------------------------------"
		print "original:     " + self.original
		print "series:       " + str(self.series)
		print "release:      " + str(self.release)
		print "year|episode: " + str(self.episode)

	def compare(self, q):
		a = re.sub("[^0-9a-z ]", " ", os.path.splitext(os.path.basename(self.original))[0], 0, re.I).lower().strip()
		b = re.sub("[^0-9a-z ]", " ", os.path.splitext(q.original)[0], 0, re.I).lower().strip()
		return a == b

class Downloader:
	def __init__(self):
		self.urls = []
		# Browser
		self.br = mechanize.Browser()
		# Cookie Jar
		self.br.set_cookiejar(cookielib.LWPCookieJar())
		self.tmpFolder = "/tmp/extract"
		self.dataFolder = "./data/"
		self.cacheFile = self.dataFolder + "cache"
		self.cache = {}
		self.configFile = self.dataFolder + "config.json"
		self.config = {}

		if not os.path.exists(self.tmpFolder):
			os.makedirs(self.tmpFolder)

		if not os.path.exists(self.dataFolder):
			os.makedirs(self.dataFolder)

		try:
			with open(self.configFile) as data_file:
				self.config = json.load(data_file)
		except ValueError:
			print "Error opening file {}. Please check json format".format(self.configFile)
			exit(1)

		if not self.login(self.config["username"], self.config["password"]):
			print "Couldn't log on. Please, check your credentials and try again."
			exit(1)

		if os.path.exists(self.cacheFile):
			self.cache = pickle.load(open(self.cacheFile, "rb"))

	def login(self, username, password):
		self.br.open("http://legendas.tv/")

		# select the first form on the page
		self.br.form = list(self.br.forms())[0]
		self.br["data[User][username]"] = username
		self.br["data[User][password]"] = password

		response = self.br.submit()		# Submit the login form
		pageHTML = response.read()

		# patternOld = 'meuperfil'
		# patternError = "rio ou senha inv"
		pattern = 'SAIR'
		matches = re.findall(pattern, pageHTML, re.I + re.MULTILINE)

		return len(matches) > 1

	def get(self, url, retry = 3):

		if url in self.cache.keys():
			return True

		# Try to download the file [retry] times
		while True:
			try:
				file = self.br.retrieve(url)[0]
				break
			except:
				if retry > 1:
					return self.get(url, retry - 1)
				return False


		# Create the tmp path if not exists
		if not os.path.exists(self.tmpFolder):
			os.makedirs(self.tmpFolder)

		# Archive(file).extractall(self.tmpFolder)
		patoolib.extract_archive(file, outdir=self.tmpFolder, verbosity=-1)

		# run tmp folder getting all str files and then erase it
		self.cache[url] = self.transverse(self.tmpFolder)
		# save this cache in a cach file
		self.save()
		return True

	def transverse(self, dir, subtitles = {}):
		for root, dirs, files in os.walk(dir):
			for file in files:
				f = os.path.join(root , file)
				if f.endswith(".srt"):
					with open(f, "r") as contentFile:
						subtitles[file] = contentFile.read()
				os.remove(f)

			for dir in dirs:
				d = os.path.join(root , dir)
				substitles = self.transverse(d, subtitles)
			os.rmdir(root)
		return subtitles

	def clear(self):
		print "Clearing cache file"
		pickle.dump({}, open(self.cacheFile, "wb"))

	def save(self):
		pickle.dump(self.cache, open(self.cacheFile, "wb"))

class SearchEngine:
	def __init__(self, d, file, application, **kwargs):
		self.lang = "1"
		self.mediaType = "-"
		self.d = d
		self.results = {}
		self.ignoreExactMatches = False
		self.retry = 3
		self.quiet = False
		self.terms = None
		self.query = File2Query()
		self.file = file

		if kwargs is not None and "retry" in kwargs.keys(): self.retry = kwargs["retry"]
		if kwargs is not None and "quiet" in kwargs.keys(): self.quiet = kwargs["quiet"]
		if kwargs is not None and "terms" in kwargs.keys(): self.terms = kwargs["terms"]

		if self.terms is None:
			self.query.parse(file)
			if not self.query.valid:
				if not self.quiet:
					print "Couldn't parse metadata from filename."
					self.setTerms(application)
			else:
				self.terms = self.query.series + ' ' + self.query.episode + ' ' + self.query.release

	def setTerms(self, application):
		if not self.quiet:
			terms = raw_input("Enter new search param to retry or enter to skip: ")
			if terms != "":
				tmp_query = File2Query()
				tmp_query.as_file = False
				tmp_query.parse( terms )

				if not tmp_query.valid:
					print "I couldn't identify the name, year of release or episode you're looking for. "
					print "My job would be easier if you give me name, year or episode and, optionally, the release. "
					print "Examples: 'Iron Man 2013 PublicHD' or 'House s01e01 IMMERSE' "
					terms = raw_input("Enter new search param to retry or enter to skip: " )
					if terms != "":
						tmp_query = File2Query()
						tmp_query.as_file = False
						tmp_query.parse( terms )

				if tmp_query.valid:
					self.query = tmp_query
					self.terms = terms
					return True
		return False

	def search(self):
		if self.terms == "": return False
		if not self.quiet: print "Terms: " + self.terms

		url =  "http://legendas.tv/legenda/busca/" + urllib.quote(self.terms) + "/" + self.lang + "/" + self.mediaType
		while True:
			try:
				self.d.br.open(url)
				break
			except:
				if self.retry > 1:
					self.retry -= 1
					return self.search()
				return False

		pattern = '<p><a href="/download/(.+?)/.+?/.+?">(.+?)</a>'
		matches = re.findall(pattern, self.d.br.response().read(), re.I + re.MULTILINE)

		if len(matches) > 1:
			if not self.quiet: print str(len(matches)) + " subtitles found. It can take a while to download it all."
		elif len(matches) == 1:
			if not self.quiet: print "Just one subtitle found"

		self.results = {}
		self.exact = False
		for id , name in matches:

			match = File2Query()
			match.as_file = False
			match.parse(name)

			if match.series == self.query.series:
				url = "http://legendas.tv/downloadarquivo/" + urllib.quote(id)
				if not self.quiet: print "Retrieving URL " + url

				if self.d.get(url):

					for key in self.d.cache[url].keys():
						match.parse(key)

						if self.ignoreExactMatches == False and self.query.compare(match):
							self.exact = True
							self.results = {key: self.d.cache[url][key]}
							return True

						if match.valid and self.query.valid:
							if match.series == self.query.series:
								if match.episode == self.query.episode:
									self.results[key] = self.d.cache[url][key]
				else:
					if not self.quiet: print "Faile to retrieve URL " + url
		return True

class Application:
	def __init__(self):
		parser = argparse.ArgumentParser(description="Grab subtitles from http://legendas.tv/")
		parser.add_argument('-d', '--dir', nargs=1,                    help="Set the directory to search media files")
		parser.add_argument('-f', '--file', nargs=1,                   help="Set a file to search subtitles for")
		parser.add_argument('-i', '--ignore', action="store_true",     help="If file found already has a subtitle, then ignore it")
		parser.add_argument('-c', '--clear', action="store_true",      help="Clear program's cache file")
		parser.add_argument('-a', '--automatic', action="store_true",  help="Don't ask questions. Just grab exact subtitles")
		parser.add_argument('-q', '--quiet', action="store_true",      help="Quiet mode")
		parser.add_argument('-u', '--username', nargs=1,               help="Username to login at legendas.tv")
		parser.add_argument('-p', '--password', nargs=1,               help="Password to login at legendas.tv")
		self.args = parser.parse_args()
		self.stop_bugging_me = False

		files = []

		if self.args.dir:
			if not self.args.quiet: print "Searching for media files in " + self.args.dir[0]
			f = FileFinder(self.args.dir[0], self)
			files = f.files
			if len(files) > 1:
				if not self.args.quiet: print str(len(files)) + " files found"
			elif len(files) == 1:
				if not self.args.quiet: print "Just one file found"
			else:
				if not self.args.quiet: print "No file found"

		if self.args.file:
			files.append(self.args.file[0])

		if self.args.clear:
			Downloader().clear()

		d = Downloader()

		for file in files:
			if not self.args.quiet: print "\nQuerying legendas.tv for " + os.path.basename(file)

			self.s = SearchEngine(d, file, self, quiet=self.args.quiet)

			while self.s.terms is not None:

				# Search the legend on Trakt.tv

				if self.s.search():

					#
					if self.args.quiet or self.args.automatic:
						if self.s.exact:
							self.move(file, sorted(self.s.results.keys())[0])
							break
					# If not quiet or automatic
					else:
						if len(self.s.results) > 0:
							if self.s.exact:
								if self.stop_bugging_me:
									self.move(file, sorted(self.s.results.keys())[0])
									break
								else:
									print "I've found the exact subtitle you're looking for: " + self.s.results.keys()[0]
									choice = self.question("Should I use it? (Y/n/a)", ("y","n","a","") )
									if choice.lower() in ("y","a",""):
										self.move(file, sorted(self.s.results.keys())[0])
										if choice.lower() == "a":
											self.stop_bugging_me = True
										break
									self.s.ignoreExactMatches = True
									continue

							else:
								print "These are the subtitles I've found for " + os.path.basename(file)
								for index, key in enumerate(sorted(self.s.results.keys())):
									print "% 2d" % (index+1) + ". " + key

								answers = map(str,range(0,len(self.s.results.keys())+2))
								answers.append("")
								choice = self.question("Choose the index for the subtitle you want and press return. Press 0 to skip. Enter to retry.", answers )
								if choice.isdigit() and int(choice) > 0:
									print sorted(self.s.results.keys())[int(choice)-1]
									self.move(file, sorted(self.s.results.keys())[int(choice)-1])
									break
								if choice.isdigit() and int(choice) == 0:
									break
								if choice == "":
									if self.s.setTerms(self):
										continue

				if not self.args.quiet: print "No subtitles found for this file."
				if not self.args.quiet and not self.args.automatic:
					if self.s.setTerms(self):
						continue
				break
		exit(0)

	def question(self, text, answers):
		while True:
			choice = raw_input(text + " (press x to quit) ")
			if choice == "x" or choice == "X":
				exit()

			for answer in answers:
				if choice == answer:
					return choice

	def move(self, file, key):
		subtitle = os.path.splitext(file)[0] + ".srt"
		if not self.args.quiet: print "Writing subtitle: " + subtitle

		content = self.s.results[key]
		with open(subtitle, 'w') as f:
			f.write(content)

def signal_handler(signal, frame):
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

Application()
