#!/usr/bin/env python

###################################################################################################
#
# Copyright (c) 2015, Armin Buescher (armin.buescher@googlemail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###################################################################################################
#
# File:		ioc-parser.py
# Desc.:	IOC Parser is a tool to extract indicators of compromise from security reports
#			in PDF format.
# Usage:	ioc-parser.py [-h] [-p INI] [-f FORMAT] PDF
# Req.:		PyPDF2 (https://github.com/mstamy2/PyPDF2)
# Author:	Armin Buescher (armin.buescher@googlemail.com)
#
###################################################################################################

import os
import sys
import fnmatch
import argparse
import ConfigParser
import StringIO
import re
import csv
import json
from PyPDF2 import PdfFileReader

class IOC_Parser(object):
	patterns = {}

	def __init__(self, format='text'):
		self.format = format

		if format == 'csv':
			self.csv_writer = csv.writer(sys.stdout, delimiter = ';')

	def load_patterns(self, fpath):
		config = ConfigParser.ConfigParser()
		with open(args.INI) as f:
			config.readfp(f)

		for ind_type in config.sections():
			ind_pattern = config.get(ind_type, 'pattern')

			if ind_pattern:
				ind_regex = re.compile(ind_pattern)
				self.patterns[ind_type] = ind_regex

	def parse(self, fpath):
		fname = os.path.basename(fpath)
		f = open(fpath, 'rb')
		pdf = PdfFileReader(f, strict = False)

		page_num = 0
		for page in pdf.pages:
			data = page.extractText()
			page_num += 1

			for ind_type, ind_regex in self.patterns.iteritems():
				matches = ind_regex.findall(data)

				for ind_match in matches:
					self.print_match(fpath, fname, page_num, ind_type, ind_match)

		f.close()

	def print_match(self, fpath, fname, page, name, match):
		if self.format == 'csv':
			self.csv_writer.writerow((fpath, page, name, match))
		elif self.format == 'json':
			data = {}
			data['path'] = fpath
			data['file'] = fname
			data['page'] = page
			data['type'] = name
			data['match'] = match
			print json.dumps(data)
		else:
			print "%s\t#%s\t%s\t%s" % (fname, page, name, match)

argparser = argparse.ArgumentParser()
argparser.add_argument('PDF', action='store', help='File/directory path to PDF report(s)')
argparser.add_argument('-p', dest='INI', default='patterns.ini', help='Pattern file')
argparser.add_argument('-f', dest='FORMAT', default='text', help='Output format (text/csv/json)')
args = argparser.parse_args()

# Assemble list of files to parse
fpath_list = []
if os.path.isfile(args.PDF):
	fpath_list = [args.PDF]
elif os.path.isdir(args.PDF):
	for walk_root, walk_dirs, walk_files in os.walk(args.PDF):
		for walk_file in fnmatch.filter(walk_files, '*.pdf'):
			fpath_list.append(os.path.join(walk_root, walk_file))
else:
	print "Error: invalid file path"

# Check output format
args.FORMAT = args.FORMAT.lower()
if not args.FORMAT in ['text', 'csv', 'json']:
	print "Error: invalid output format"
	args.FORMAT = 'text'

# Initialize parser
parser = IOC_Parser(args.FORMAT)
parser.load_patterns(args.INI)

# Parse files
for fpath in fpath_list:
	result = parser.parse(fpath)