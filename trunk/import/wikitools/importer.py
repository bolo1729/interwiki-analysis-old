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

import gzip, logging, os, re, sys

class Importer:
	NAMESPACES = (0, 14)

	def __init__(self, dataSource = None, dataRepository = None):
		self.log = logging.getLogger('Importer')
		# self.logValidator = logging.getLogger('DataValidator')
		self.dataSource = dataSource
		self.dataRepository = dataRepository

	def processPages(self, lang, records):
		for record in records:
			id = record[0]
			namespace = record[1]
			title = record[2]

			if not int(namespace) in self.NAMESPACES:
				continue
			self.dataRepository.insertPage(lang, id, namespace, title)

	def processRedirects(self, lang, records):
		for record in records:
			fromId = record[0]
			toNamespace = record[1]
			toTitle = record[2]

			if not int(toNamespace) in self.NAMESPACES:
				continue

			page = self.dataRepository.getPage(lang + ':' + fromId)
			if page == None:
				# self.logValidator.warn('Nonexistent redirect source [%s] (language %s)' % (fromId, lang))
				continue
			fromNamespace = page['namespace']

			if int(fromNamespace) != int(toNamespace):
				# self.logValidator.warn('Redirect to a different namespace from %s:%s (%s to %s)' % (page['lang'], page['title'], fromNamespace, toNamespace))
				continue

			toKey = self.dataRepository.getPageKey(lang, toNamespace, toTitle)
			if toKey == None:
				# self.logValidator.warn('Nonexistent redirect target %s:%s (namespace %s)' % (lang, toTitle, toNamespace))
				continue

			self.dataRepository.insertRedirect(lang + ':' + fromId, toKey)

	def processLanglinks(self, fromLang, records):
		for record in records:
			fromId = record[0]
			toLang = record[1]
			toTitle = record[2]

			if fromLang == toLang:
				# self.logValidator.warn('Langlink to the same language to %s:%s (namespace %s)' % (lang, toTitle, toNamespace))
				continue

			page = self.dataRepository.getPage(fromLang + ':' + fromId)
			if page == None:
				continue
			if page['redirect'] != None:
				# self.logValidator.warn('Langlink from a redirect source %s:%s (namespace %s)' % (page['lang'], page['title'], page['namespace']))
				continue
			namespace = page['namespace']

			if int(namespace) != 0:
				toTitle = ':'.join(toTitle.split(':')[1:])

			toKey = self.dataRepository.getPageKey(toLang, namespace, toTitle)
			if toKey == None:
				# self.logValidator.warn('Nonexistent langlink target %s:%s (namespace %s)' % (toLang, toTitle, namespace))
				continue

			self.dataRepository.insertLanglink(fromLang + ':' + fromId, toKey)

	def processPagelinks(self, lang, records):
		for record in records:
			fromId = record[0]
			toNamespace = record[1]
			toTitle = record[2]

			fromPage = self.dataRepository.getPage(lang + ':' + fromId)
			if fromPage == None:
				continue
			fromNamespace = fromPage['namespace']

			toKey = self.dataRepository.getPageKey(lang, toNamespace, toTitle)
			if toKey == None:
				# self.logValidator.warn('Nonexistent pagelink target %s:%s (namespace %s)' % (toLang, toTitle, toNamespace))
				continue

			self.dataRepository.insertPagelink(lang + ':' + fromId, toKey)

	def processCategorylinks(self, lang, records):
		for record in records:
			fromId = record[0]
			toTitle = record[1]

			fromPage = self.dataRepository.getPage(lang + ':' + fromId)
			if fromPage == None:
				continue
			fromNamespace = fromPage['namespace']

			toNamespace = '14'
			toKey = self.dataRepository.getPageKey(lang, toNamespace, toTitle)
			if toKey == None:
				# self.logValidator.warn('Nonexistent categorylink target %s:%s (namespace %s)' % (toLang, toTitle, toNamespace))
				continue

			self.dataRepository.insertCategorylink(lang + ':' + fromId, toKey)

	def doImport(self):
		langs = self.dataSource.getLangs()
		if len(langs) > 0:
			self.log.info('Processing %d language(s): %s' % (len(langs), ' '.join(langs)))
		else:
			self.log.error('No languages fround')
			return

		for lang in langs:
			self.log.info('Importing pages from ' + lang)
			self.dataRepository.connect()
			self.dataSource.importTable(lang, 'page', lambda r : self.processPages(lang, r))
			self.dataRepository.disconnect()

		for lang in langs:
			self.log.info('Importing redirects from ' + lang)
			self.dataRepository.connect()
			self.dataSource.importTable(lang, 'redirect', lambda r : self.processRedirects(lang, r))
			self.dataRepository.disconnect()

		self.log.info('Removing double redirects')
		self.dataRepository.connect()
		self.dataRepository.removeDoubleRedirects()
		self.dataRepository.disconnect()

		for lang in langs:
			self.log.info('Importing langlinks from ' + lang)
			self.dataRepository.connect()
			self.dataSource.importTable(lang, 'langlinks', lambda r : self.processLanglinks(lang, r))
			self.dataRepository.disconnect()

		self.log.info('Finding connected components')
		self.dataRepository.connect()
		self.dataRepository.findConnectedComponents()
		self.dataRepository.disconnect()

		for lang in langs:
			self.log.info('Importing pagelinks from ' + lang)
			self.dataRepository.connect()
			self.dataSource.importTable(lang, 'pagelinks', lambda r : self.processPagelinks(lang, r))
			self.dataRepository.disconnect()

		for lang in langs:
			self.log.info('Importing categorylinks from ' + lang)
			self.dataRepository.connect()
			self.dataSource.importTable(lang, 'categorylinks', lambda r : self.processCategorylinks(lang, r))
			self.dataRepository.disconnect()

		self.log.info('Done')

class DummyDataSource:
	def getLangs(self):
		return []
	def importTable(self, lang, type, callback):
		pass

class DumpsDataSource:
	def __init__(self, dumpsDir = None):
		self.dumpsDir = dumpsDir

	def getLangs(self):
		langs = []
		for filename in os.listdir(self.dumpsDir):
			match = re.match(r'(?P<lang>[a-z]+(_[a-z]+(_[a-z]+)?)?)wiki-\d{8}-page.sql.gz', filename)
			if not match:
				continue
			langs += [match.group('lang').replace('_', '-')]
		return sorted(langs)

	def importTable(self, lang, type, callback):
		source = None
		for filename in os.listdir(self.dumpsDir):
			match = re.match(r'(?P<lang>[a-z]+(_[a-z]+(_[a-z]+)?)?)wiki-(?P<date>\d{8})-(?P<type>[a-z]+).sql.gz', filename)
			if not match or lang != match.group('lang').replace('_', '-') or type != match.group('type'):
				continue
			source = gzip.open(self.dumpsDir + os.sep + filename)
			break
		if not source:
			raise Exception, 'No such file'
		for line in source:
			if not line.startswith('INSERT INTO'):
				continue
			self.importLine(line, callback)

	def importLine(self, line, callback):
		cur = 0
		records = []
		while True:
			(record, valid) = ([], True)
			cur = line.find('(', cur)
			if cur == -1:
				break
			cur += 1

			while True:
				type = None
				if line[cur] == '\'':
					type = '\''
				if line[cur] == '"':
					type = '"'

				if not type:
					start = cur
					nextComma = line.find(',', cur)
					if nextComma == -1:
						nextComma = sys.maxint
					nextBracket = line.find(')', cur)
					if nextBracket == -1:
						nextBracket = sys.maxint
					end = min(nextComma, nextBracket)
					if end == sys.maxint:
						raise Exception, 'Unexpected end of line'
					
					record += [line[start:end].replace('_', ' ')]
					cur = end + 1
					if line[cur - 1] == ')':
						break
				else:
					cur += 1
					start = cur
					while True:
						cur = line.find(type, cur)
						if cur == -1:
							raise Exception, 'Unexpected end of line'
						backslashes = 0
						while line[cur - 1 - backslashes] == '\\':
							backslashes += 1
						if backslashes % 2 == 0:
							break
						cur += 1
					
					end = cur
					cur += 1
					if line[cur] != ',' and line[cur] != ')':
						raise Exception
					cur += 1
					text = line[start:end].replace('\\\'', '\'').replace('\\\"', '\"').replace('\\\\', '\\').replace('_', ' ')
					try:
						text = text.decode('utf-8')
					except UnicodeDecodeError:
						valid = False
					record += [text]
					if line[end + 1] == ')':
						break
			if valid:
				records += [record]
		callback(records)
