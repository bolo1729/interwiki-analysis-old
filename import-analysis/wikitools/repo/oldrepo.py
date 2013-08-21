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

class OldRepository:
    def __init__(self, host = None, port = None, database = None, user = None, password = None, cache = False, prefix = ''):
        self.dbHost = host
        self.dbPort = port
        self.dbDatabase = database
        self.dbUser = user
        self.dbPassword = password
        self.log = logging.getLogger('OldRepository')
        self.cache = cache
        self.prefix = prefix
        self.pages = {}
        self.pageKeys = {}

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

    def getIncoherent(self):
        cur = self.conn.cursor()
        cur.execute('SELECT key FROM %scomp WHERE NOT coherent' % self.prefix)
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
        cur.execute('SELECT key, lang, title FROM %snode WHERE comp_id = %%s' % self.prefix, (compKey,))
        rows = cur.fetchall()
        cur.close()
        pages = {}
        if not rows:
            return pages
        for row in rows:
            pages[row[0]] = {'key': row[0], 'lang': row[1], 'namespace': '0', 'title': row[2], 'redirect': None, 'comp': compKey}
        return pages

    def getComponentLanglinks(self, compKey):
        cur = self.conn.cursor()
        cur.execute('SELECT src_id, dst_id FROM %slink WHERE comp_id = %%s' % self.prefix, (compKey,))
        rows = cur.fetchall()
        cur.close()
        links = []
        if not rows:
            return links
        for row in rows:
            links += [(row[0], row[1])]
        return links

    def getPageKey(self, lang, namespace, title):
        return None
    def getPage(self, key):
        return None
    def insertPage(self, lang, id, namespace, title):
        pass
    def insertRedirect(self, fromKey, toKey):
        pass
    def removeDoubleRedirects(self):
        pass
    def insertLanglink(self, fromKey, toKey):
        pass
    def findConnectedComponents(self):
        pass
    def insertPagelink(self, fromKey, toKey):
        pass
    def insertCategorylink(self, fromKey, toKey):
        pass
    def deletePagePositions(self, compKey):
        pass
    def insertPagePosition(self, pageKey, compKey, position):
        pass
    def getComponentPagePositions(self, compKey):
        return {}
    def deletePageMeanings(self, auth, compKey):
        pass
    def insertPageMeanings(self, auth, meaningKey, compKey, pageKeys):
        pass
    def getComponentPageMeanings(self, compKey, auth):
        return {}
    def countCommonCategories(self, aKey, bKey):
        return 0
    def countCommonLinks(self, aKey, bKey):
        return 0
