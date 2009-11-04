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

import logging, uuid

class BigMemoryPostgresqlRepository:

	def __init__(self, host = None, port = None, database = None, user = None, password = None, cache = False):
		self.dbHost = host
		self.dbPort = port
		self.dbDatabase = database
		self.dbUser = user
		self.dbPassword = password
		self.log = logging.getLogger('BigMemoryPostgresqlRepository')

		self.BLOCK = 16384
		self.capacity = 1
		self.size = 1
		self.keys = [None]
		self.lnts = [None]
		self.redirects = [None]
		self.components = [None]
		self.langlinks = [None]

		self.byLNT = {}
		self.byKey = {}
		self.revRedirects = {}

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
		lnt = lang + ":" + namespace + ":" + title.encode('utf-8')
		if lnt in self.byLNT:
			idx = self.byLNT[lnt]
			return self.keys[idx]
		return None

	def getPage(self, key):
		if key in self.byKey:
			idx = self.byKey[key]
			lnt = self.lnts[idx]
			lang = key.split(":")[0]
			namespace = lnt.split(":")[1]
			title = ":".join(lnt.split(":")[2:])
			redirect = self.redirects[idx]
			component = self.components[idx]
			return {'key': key, 'lang': lang, 'namespace': namespace, 'title': title.decode('utf-8'), 'redirect': redirect, 'component': component}
		return None

	def insertPage(self, lang, id, namespace, title):
		if self.size == self.capacity:
			self.keys += self.BLOCK*[None]
			self.lnts += self.BLOCK*[None]
			self.redirects += self.BLOCK*[None]
			self.components += self.BLOCK*[None]
			self.langlinks += self.BLOCK*[None]
			self.capacity += self.BLOCK

		key = lang + ':' + id
		key = intern(key)
		lnt = lang + ":" + namespace + ":" + title.encode('utf-8')
		self.byKey[key] = self.size
		self.byLNT[lnt] = self.size

		self.keys[self.size] = key
		self.lnts[self.size] = lnt
		self.redirects[self.size] = None
		self.components[self.size] = None
		self.langlinks[self.size] = None

		self.size += 1

	def insertRedirect(self, fromKey, toKey):
		if fromKey in self.byKey:
			idxFrom = self.byKey[fromKey]
			idxTo = self.byKey[toKey]
			self.redirects[idxFrom] = toKey

	def removeDoubleRedirects(self):
		sources = {}
		for i in xrange(1, self.size):
			if self.redirects[i] != None:
				sources[self.keys[i]] = True
		for i in xrange(1, self.size):
			target = self.redirects[i]
			if target != None and target in sources:
				self.redirects[i] = None
		for i in xrange(1, self.size):
			if self.redirects[i] != None:
				j = self.byKey[self.redirects[i]]
				if not j in self.revRedirects:
					self.revRedirects[j] = []
				self.revRedirects[j] += [i]

	def insertLanglink(self, fromKey, toKey):
		idxFrom = self.byKey[fromKey]
		idxTo = self.byKey[toKey]
		if self.langlinks[idxFrom] == None:
			self.langlinks[idxFrom] = set()
		if self.langlinks[idxTo] == None:
			self.langlinks[idxTo] = set()

		if (-idxTo) in self.langlinks[idxFrom]:
			self.langlinks[idxFrom] -= set([-idxTo])
		self.langlinks[idxFrom] |= set([idxTo])
		if not idxFrom in self.langlinks[idxTo]:
			self.langlinks[idxTo] |= set([-idxFrom])

	def findConnectedComponents(self):
		visited = self.size * [False]
		for idx in xrange(1, self.size):
			if visited[idx]:
				continue
			self.log.debug('start: %s' % self.keys[idx])
			page = self.getPage(self.keys[idx])
			cur = self.conn.cursor()
			if self.langlinks[idx] == None and self.redirects[idx] == None and not idx in self.revRedirects:
				# This is an isolated page: store it and continue
				visited[idx] = True
				cur.execute('INSERT INTO network_page (key, lang, namespace, title, redirect_id, comp_id) VALUES (%s, %s, %s, %s, %s, %s)', (page['key'], page['lang'], page['namespace'], page['title'], page['redirect'], None))
				cur.close()
				continue

			nodes = set([idx])
			queue = [idx]
			links = []
			while len(queue) > 0:
				i, queue = queue[0], queue[1:]
				if self.langlinks[i] != None:
					for j in self.langlinks[i]:
						if j > 0:
							links += [(i, j)]
						j = abs(j)
						if j in nodes:
							continue
						nodes |= set([j])
						queue += [j]
						self.log.debug('through langlink: %s' % self.keys[j])
				if self.redirects[i] != None:
					j = self.byKey[self.redirects[i]]
					if not j in nodes:
						nodes |= set([j])
						queue += [j]
						self.log.debug('through redirect: %s' % self.keys[j])
				if i in self.revRedirects:
					for j in self.revRedirects[i]:
						if not j in nodes:
							nodes |= set([j])
							queue += [j]
							self.log.debug('through rev. redirect: %s' % self.keys[j])

			keys = [self.keys[i] for i in nodes]
			self.log.debug('keys = %s' % keys)
			coherent, langs = True, set()
			for key in keys:
				p = self.getPage(key)
				if p['redirect'] != None:
					continue
				if p['lang'] in langs:
					coherent = False
					break
				langs |= set([p['lang']])

			comp = None
			if len(links) > 0:
				comp = str(uuid.uuid5(uuid.NAMESPACE_DNS, "".join(sorted(keys))))

			for i in nodes:
				self.components[i] = comp

			size = 0
			for i in nodes:
				if self.redirects[i] == None:
					size += 1

			for i in nodes:
				visited[i] = True

			# Store the component
			if comp != None:
				self.log.info('Storing component %s', comp)
				cur.execute('INSERT INTO network_comp (key, namespace, coherent, size) VALUES (%s, %s, %s, %s)', (comp, page['namespace'], coherent, size))
			for i in nodes:
				p = self.getPage(self.keys[i])
				key = p['key']
				lang = p['lang']
				namespace = p['namespace']
				title = p['title']
				redirect = p['redirect']
				# self.log.debug('page = %s' % p)
				self.cursor.execute('INSERT INTO network_page (key, lang, namespace, title, redirect_id, comp_id) VALUES (%s, %s, %s, %s, %s, %s)', (key, lang, namespace, title, redirect, comp))
			for (i, j) in links:
				fromKey = self.keys[i]
				toKey = self.keys[j]
				cur.execute('INSERT INTO network_langlink (src_id, dst_id, comp_id) VALUES (%s, %s, %s)', (fromKey, toKey, comp))

			cur.close()
			self.conn.commit()

	def insertPagelink(self, fromKey, toKey):
		self.cursor.execute('INSERT INTO network_pagelink (src_id, dst_id) VALUES (%s, %s)', (fromKey, toKey))

	def insertCategorylink(self, fromKey, toKey):
		self.cursor.execute('INSERT INTO network_categorylink (page_id, category_id) VALUES (%s, %s)', (fromKey, toKey))

	def getIncoherent(self, limit = None):
		cur = self.conn.cursor()
		if not limit:
			cur.execute('SELECT key FROM network_comp WHERE NOT coherent')
		else:
			cur.execute('SELECT key FROM network_comp WHERE NOT coherent AND size <= %s', (limit,))
		rows = cur.fetchall()
		cur.close()
		keys = []
		if rows == None:
			return keys
		for row in rows:
			keys += [row[0]]
		return keys
	
	def getComponentPages(self, compKey):
		cur = self.conn.cursor()
		cur.execute('SELECT key, lang, namespace, title, redirect_id FROM network_page WHERE comp_id = %s', (compKey,))
		rows = cur.fetchall()
		cur.close()
		pages = {}
		if not rows:
			return pages
		for row in rows:
			pages[row[0]] = {'key': row[0], 'lang': row[1], 'namespace': row[2], 'title': row[3], 'redirect': row[4], 'comp': compKey}
		return pages

	def getComponentLanglinks(self, compKey):
		cur = self.conn.cursor()
		cur.execute('SELECT src_id, dst_id FROM network_langlink WHERE comp_id = %s', (compKey,))
		rows = cur.fetchall()
		cur.close()
		links = []
		if not rows:
			return links
		for row in rows:
			links += [(row[0], row[1])]
		return links

	def deletePagePositions(self, compKey):
		self.cursor.execute('DELETE FROM network_pageposition WHERE comp_id = %s', (compKey,))

	def insertPagePosition(self, pageKey, compKey, position):
		self.cursor.execute('INSERT INTO network_pageposition (page_id, x, y, z, comp_id) VALUES (%s, %s, %s, %s, %s)', (pageKey, str(position[0]), str(position[1]), str(position[2]), compKey))
	
	def getComponentPagePositions(self, compKey):
		cur = self.conn.cursor()
		cur.execute('SELECT page_id, x, y, z FROM network_pageposition WHERE comp_id = %s', (compKey,))
		rows = cur.fetchall()
		cur.close()
		pages = {}
		if not rows:
			return pages
		for row in rows:
			pages[row[0]] = (float(row[1]), float(row[2]), float(row[3]))
		return pages

	def deletePageMeanings(self, auth, compKey):
		self.cursor.execute('DELETE FROM network_pagemeaning WHERE comp_id = %s AND auth = %s', (compKey, auth))

	def insertPageMeanings(self, auth, meaningKey, compKey, pageKeys):
		for pageKey in pageKeys:
			self.cursor.execute('INSERT INTO network_pagemeaning (auth, page_id, meaning, comp_id) VALUES (%s, %s, %s, %s)', (auth, pageKey, meaningKey, compKey))

	def getComponentPageMeanings(self, compKey, auth):
		cur = self.conn.cursor()
		cur.execute('SELECT page_id, meaning FROM network_pagemeaning WHERE comp_id = %s AND auth = %s', (compKey, auth))
		rows = cur.fetchall()
		cur.close()
		pages = {}
		if not rows:
			return pages
		for row in rows:
			pages[row[0]] = row[1]
		return pages

	def countCommonCategories(self, aKey, bKey):
		cur = self.conn.cursor()
		cur.execute('SELECT COUNT(*) FROM '
			+ ' ((SELECT dst_id FROM network_langlink WHERE src_id IN (SELECT category_id FROM network_categorylink WHERE page_id = %s))'
			+ ' INTERSECT (SELECT category_id FROM network_categorylink WHERE page_id = %s)) AS foo',
			(aKey, bKey))
		row = cur.fetchone()
		cur.close()
		# self.log.debug('Found %s common categories between %s and %s' % (row[0], aKey, bKey))
		return int(row[0])

	def countCommonLinks(self, aKey, bKey):
		cur = self.conn.cursor()
		cur.execute('SELECT COUNT(*) FROM '
			+ ' ((SELECT dst_id FROM network_langlink WHERE src_id IN (SELECT dst_id FROM network_pagelink WHERE src_id = %s))'
			+ ' INTERSECT (SELECT dst_id FROM network_pagelink WHERE src_id = %s)) AS foo',
			(aKey, bKey))
		row = cur.fetchone()
		cur.close()
		# self.log.debug('Found %s common links between %s and %s' % (row[0], aKey, bKey))
		return int(row[0])
