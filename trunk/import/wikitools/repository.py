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
