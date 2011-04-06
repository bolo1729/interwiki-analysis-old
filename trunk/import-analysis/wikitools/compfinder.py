# Interwiki analysis tools
# Copyright (C) 2007-2011  Lukasz Bolikowski
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

import array, bisect, logging, uuid

class PageIndex:
	def __init__(self):
		self.log = logging.getLogger('PageIndex')
		self.pageKeys = {}

	def addPage(self, key):
		lang, id = key.split(':')
		if lang not in self.pageKeys:
			self.pageKeys[lang] = []
		self.pageKeys[lang].append(int(id))

	def postAdd(self):
		self.langs = sorted(self.pageKeys)
		self.offsets = {}
		self.size = 0
		for lang in self.langs:
			self.offsets[lang] = self.size
			self.size += len(self.pageKeys[lang])
			self.pageKeys[lang].sort()
		self.redirects = self.size * [False]
		self.links = self.size * [None]
		self.visited = self.size * [False]

	def getIndex(self, key):
		lang, id = key.split(':')
		ids = self.pageKeys[lang]
		idx = bisect.bisect_left(ids, int(id))
		if idx != len(ids) and ids[idx] == int(id):
			return self.offsets[lang] + idx
		raise Exception

	def getLangAndKey(self, index):
		for lang in self.langs:
			off, siz = self.offsets[lang], len(self.pageKeys[lang])
			if off <= index and index < off + siz:
				return lang, lang + ':' + str(self.pageKeys[lang][index - off])
		raise Exception

	def connect(self, src, dst):
		if self.links[src] is None:
			self.links[src] = array.array('i')
		if self.links[dst] is None:
			self.links[dst] = array.array('i')
		self.links[src].append(dst)
		self.links[dst].append(src)

	def addRedirect(self, keyFrom, keyTo):
		fi = self.getIndex(keyFrom)
		ti = self.getIndex(keyTo)
		self.redirects[fi] = True
		self.connect(fi, ti)

	def addLangLink(self, keyFrom, keyTo):
		fi = self.getIndex(keyFrom)
		ti = self.getIndex(keyTo)
		self.connect(fi, ti)

	def doFindComponents(self):
		for si in xrange(self.size):
			if self.visited[si]:
				continue
			nodes = [si]
			queue = [si]
			self.visited[si] = True
			while queue:
				node, queue = queue[0], queue[1:]
				if not self.links[node]:
					continue
				for n in self.links[node]:
					if not self.visited[n]:
						nodes.append(n)
						queue.append(n)
						self.visited[n] = True
	
			pageKeys, langsVisited, totalCount, coherent = [], set(), 0, True
			for node in nodes:
				lang, key = self.getLangAndKey(node)
				pageKeys.append(key)
				if self.redirects[node]:
					continue
				if lang in langsVisited:
					coherent = False
				else:
					langsVisited |= set([lang])
				totalCount += 1
			
			if totalCount == 1:
				continue

			pageKeys.sort()
			compKey = str(uuid.uuid5(uuid.NAMESPACE_OID, '#'.join(pageKeys)))

			yield compKey, pageKeys, coherent, totalCount

class ComponentFinder:
	def __init__(self, repo):
		self.log = logging.getLogger('ComponentFinder')
		self.repo = repo
		self.pageIndex = PageIndex()

	def doFindComponents(self):
		self.repo.connect()

		self.log.info('Loading pages')
		for key in self.repo.getAllPageKeys():
			self.pageIndex.addPage(key)

		self.log.info('Indexing pages')
		self.pageIndex.postAdd()

		self.log.info('Loading redirects')
		for keyFrom, keyTo in self.repo.getAllRedirects():
			self.pageIndex.addRedirect(keyFrom, keyTo)

		self.log.info('Loading language links')
		for keyFrom, keyTo in self.repo.getAllLangLinks():
			self.pageIndex.addLangLink(keyFrom, keyTo)

		self.log.info('Finding components')
		for compKey, pageKeys, coherent, size in self.pageIndex.doFindComponents():
			self.repo.saveComponent(compKey, pageKeys, coherent, size)

		self.repo.disconnect()

