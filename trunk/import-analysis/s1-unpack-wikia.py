#!/usr/bin/python
# Interwiki analysis tools
# Copyright (C) 2007-2009  Lukasz Bolikowski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# This script converts a database dump set like:
#   ensomename.sql
#   desomename.sql
#   frsomename.sql
#   ...
# to the form in which the Wikipedia dumps are provided, i.e.:
#   enwiki-00000000-page.sql.gz
#   enwiki-00000000-redirects.sql.gz
#   ...
#   dewiki-00000000-page.sql.gz
#   ...
# The output files contain only the INSERT statements.  All the files
# are read from and written to the current working directory.
# The script requires exactly one argument: the infix appearing in the
# input files.  For the example above, the argument should be: somename

import gzip, os, re

class WikiaUnpacker:
	def __init__(self, wiki = None):
		self.wiki = wiki

	def getLangs(self):
		langs = []
		for filename in os.listdir('.'):
			match = re.match(r'(?P<lang>[a-z]+(_[a-z]+(_[a-z]+)?)?)' + self.wiki + '.sql', filename)
			if not match:
				continue
			langs += [match.group('lang').replace('_', '-')]
		return sorted(langs)

	def unpack(self):
		langs = self.getLangs()
		for lang in langs:
			src = open(lang + self.wiki + '.sql')
			dst = None
			for line in src:
				match = re.match(r'-- Table structure for table `(?P<table>[a-z]+)`', line)
				if match:
					if dst: dst.close()
					table = match.group('table')
					dst = gzip.open(lang.replace('-', '_') + 'wiki-00000000-' + table + '.sql.gz', 'w')
				if line.startswith('INSERT INTO'):
					dst.write(line)
			if dst: dst.close()
			src.close()
			

if __name__ == "__main__":
	import sys
	if len(sys.argv) < 2:
		print 'Usage: ' + sys.argv[0] + ' <wiki-name>'
		sys.exit(1)
	wiki = sys.argv[1]
	unpacker = WikiaUnpacker(wiki)
	unpacker.unpack()

