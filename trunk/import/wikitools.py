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

import gzip, logging, os, re, sys, uuid

NAMESPACES = (0, 14)

class Importer:
	def __init__(self, dataSource = None, dataRepository = None):
		self.log = logging.getLogger('Importer')
		self.dataSource = dataSource
		self.dataRepository = dataRepository

	def processPages(self, lang, records):
		for record in records:
			id = record[0]
			namespace = record[1]
			title = record[2]

			if not int(namespace) in NAMESPACES:
				continue
			self.dataRepository.insertPage(lang, id, namespace, title)

	def processRedirects(self, lang, records):
		for record in records:
			fromId = record[0]
			toNamespace = record[1]
			toTitle = record[2]

			if not int(toNamespace) in NAMESPACES:
				continue

			page = self.dataRepository.getPage(lang + ':' + fromId)
			if page == None:
				continue
			fromNamespace = page['namespace']

			if int(fromNamespace) != int(toNamespace):
				continue

			toKey = self.dataRepository.getPageKey(lang, toNamespace, toTitle)
			if toKey == None:
				# self.log.warn('Nonexistent target %s:%s (namespace %s)' % (lang, toTitle, toNamespace))
				continue

			self.dataRepository.insertRedirect(lang + ':' + fromId, toKey)

	def processLanglinks(self, fromLang, records):
		for record in records:
			fromId = record[0]
			toLang = record[1]
			toTitle = record[2]

			if fromLang == toLang:
				continue

			page = self.dataRepository.getPage(fromLang + ':' + fromId)
			if page == None or page['redirect'] != None:
				continue
			namespace = page['namespace']

			if int(namespace) != 0:
				toTitle = ':'.join(toTitle.split(':')[1:])

			toKey = self.dataRepository.getPageKey(toLang, namespace, toTitle)
			if toKey == None:
				# self.log.warn('Nonexistent target %s:%s (namespace %s)' % (toLang, toTitle, namespace))
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
				# self.log.warn('Nonexistent target %s:%s (namespace %s)' % (toLang, toTitle, toNamespace))
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

			toKey = self.dataRepository.getPageKey(lang, '14', toTitle)
			if toKey == None:
				# self.log.warn('Nonexistent target %s:%s (namespace %s)' % (toLang, toTitle, toNamespace))
				continue

			self.dataRepository.insertCategorylink(lang + ':' + fromId, toKey)

	def doImport(self):
		langs = self.dataSource.getLangs()
		self.log.info('Processing %d language(s): %s' % (len(langs), ' '.join(langs)))

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

class DummyDataRepository:
	def connect(self):
		pass
	def disconnect(self):
		pass
	def findConnectedComponents(self):
		pass
	def getPage(self, key):
		return None
	def getPageKey(self, lang, namespace, title):
		return None
	def insertCategorylink(self, fromKey, toKey):
		pass
	def insertLanglink(self, fromKey, toKey):
		pass
	def insertPage(self, lang, id, namespace, title):
		pass
	def insertPagelink(self, fromKey, toKey):
		pass
	def insertRedirect(self, fromKey, toKey):
		pass
	def removeDoubleRedirects(self):
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

class PostgresqlRepository:
	def __init__(self, host = None, port = None, database = None, user = None, password = None):
		self.dbHost = host
		self.dbPort = port
		self.dbDatabase = database
		self.dbUser = user
		self.dbPassword = password

	def connect(self):
		args = {}
		if self.dbHost != None:
			args['host'] = self.dbHost
		if self.dbPort != None:
			args['port'] = self.dbPort
		if self.dbDatabase != None:
			args['database'] = self.dbDatabase
		if self.dbUser != None:
			args['user'] = self.dbUser
		if self.dbPassword != None:
			args['password'] = self.dbPassword

		import psycopg2

		self.conn = psycopg2.connect(**args)
		self.cursor = self.conn.cursor()

	def disconnect(self):
		self.cursor.close()
		self.conn.commit()
		self.conn.close()
		(self.cursor, self.conn) = (None, None)

	def getPageKey(self, lang, namespace, title):
		cur = self.conn.cursor()
		cur.execute('SELECT key FROM network_page WHERE lang = %s AND namespace = %s AND title = %s', (lang, namespace, title))
		row = cur.fetchone()
		cur.close()
		if not row:
			return None
		return row[0]

	def getPage(self, key):
		cur = self.conn.cursor()
		cur.execute('SELECT lang, namespace, title, redirect_id FROM network_page WHERE key = %s', (key,))
		row = cur.fetchone()
		cur.close()
		if not row:
			return None
		return {'lang': row[0], 'namespace': row[1], 'title': row[2], 'redirect': row[3]}

	def insertPage(self, lang, id, namespace, title):
		self.cursor.execute('INSERT INTO network_page (key, lang, namespace, title) VALUES (%s, %s, %s, %s)', (lang + ':' + id, lang, namespace, title))

	def insertRedirect(self, fromKey, toKey):
		self.cursor.execute('UPDATE network_page SET redirect_id = %s WHERE key = %s', (toKey, fromKey))

	def removeDoubleRedirects(self):
		self.cursor.execute('UPDATE network_page SET redirect_id = NULL WHERE key IN (SELECT DISTINCT a.redirect_id AS r FROM (SELECT * FROM network_page WHERE redirect_id IS NOT NULL) AS a JOIN network_page AS b ON (a.redirect_id = b.key) WHERE b.redirect_id IS NOT NULL)')


	def insertLanglink(self, fromKey, toKey):
		self.cursor.execute('INSERT INTO network_langlink (src_id, dst_id) VALUES (%s, %s)', (fromKey, toKey))

	def findConnectedComponents(self):
		while True:
			cur = self.conn.cursor()
			cur.execute('SELECT src_id FROM network_langlink WHERE comp_id IS NULL LIMIT 1')
			row = cur.fetchone()
			cur.close()

			if not row:
				break

			compKey = str(uuid.uuid4())
			cur = self.conn.cursor()
			sourceKey = row[0]
			sourcePage = self.getPage(sourceKey)
			sourceNamespace = sourcePage['namespace']
			cur.execute('INSERT INTO network_comp (key, namespace) VALUES (%s, %s)', (compKey, sourceNamespace))
			cur.execute('UPDATE network_page SET comp_id = %s WHERE key = %s', (compKey, sourceKey))
			while True:
				cur.execute('UPDATE network_langlink '
					+ ' SET comp_id = %s '
					+ ' WHERE src_id IN (SELECT key FROM network_page WHERE comp_id = %s)',
					(compKey, compKey))
				cur.execute('UPDATE network_langlink '
					+ ' SET comp_id = %s '
					+ ' WHERE dst_id IN (SELECT key FROM network_page WHERE comp_id = %s)',
					(compKey, compKey))
				updatedPages = 0
				cur.execute('UPDATE network_page '
					+ ' SET comp_id = %s '
					+ ' WHERE (comp_id IS NULL) AND key IN '
					+ '   (SELECT src_id AS k FROM network_langlink WHERE comp_id = %s '
					+ '   UNION SELECT dst_id AS k FROM network_langlink WHERE comp_id = %s '
					+ '   UNION SELECT redirect_id AS k FROM network_page WHERE comp_id = %s)',
					(compKey, compKey, compKey, compKey))
				updatedPages += cur.rowcount
				cur.execute('UPDATE network_page '
					+ ' SET comp_id = %s '
					+ ' WHERE (comp_id IS NULL) AND redirect_id IN '
					+ '   (SELECT key AS k FROM network_page WHERE comp_id = %s)',
					(compKey, compKey))
				updatedPages += cur.rowcount
				if updatedPages == 0:
					break

			cur.execute('UPDATE network_comp SET '
				+ ' coherent = (SELECT COUNT(*) = 0 AS answer '
				+ '   FROM (SELECT lang AS c FROM network_page '
				+ '     WHERE comp_id = %s AND redirect_id IS NULL '
				+ '     GROUP BY lang HAVING COUNT(*) > 1) AS foo),'
				+ ' size = (SELECT COUNT(*) FROM network_page WHERE comp_id = %s AND redirect_id IS NULL) '
				+ ' WHERE key = %s', (compKey, compKey, compKey))

			cur.close()

	def insertPagelink(self, fromKey, toKey):
		self.cursor.execute('INSERT INTO network_pagelink (src_id, dst_id) VALUES (%s, %s)', (fromKey, toKey))

	def insertCategorylink(self, fromKey, toKey):
		self.cursor.execute('INSERT INTO network_categorylink (page_id, category_id) VALUES (%s, %s)', (fromKey, toKey))

