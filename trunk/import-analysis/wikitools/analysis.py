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

import logging, math, numpy, os, random, scipy.optimize, sys, uuid

class PagePositionCalculator:
	INITBOX = 10.0
	R = 1.0
	REPULSIVE = 100.0
	CATFACTOR = 2.0
	LNKFACTOR = 0.5
	
	def __init__(self, dataRepository = None):
		self.log = logging.getLogger('PagePositionCalculator')
		self.dataRepository = dataRepository

	def minimizedFunction(self, positions, pages, revPages, idxLangs, idxLinks, idxRedirects):
		value = 0.0
		for aIdx, bIdx in idxLinks:
			aX = positions[3*aIdx + 0]
			aY = positions[3*aIdx + 1]
			aZ = positions[3*aIdx + 2]
			
			bX = positions[3*bIdx + 0]
			bY = positions[3*bIdx + 1]
			bZ = positions[3*bIdx + 2]
			
			r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY) + (aZ - bZ)*(aZ - bZ)
			r = math.sqrt(r2)
			weight = idxLinks[(aIdx, bIdx)]
			weight = weight * weight * weight
			value += weight * (r - self.R) * (r - self.R)

		for lang in idxLangs:
			for aIdx in idxLangs[lang]:
				for bIdx in idxLangs[lang]:
					if aIdx == bIdx:
						continue
					if idxRedirects[aIdx] == idxRedirects[bIdx]:
						continue
					aX = positions[3*aIdx + 0]
					aY = positions[3*aIdx + 1]
					aZ = positions[3*aIdx + 2]
			
					bX = positions[3*bIdx + 0]
					bY = positions[3*bIdx + 1]
					bZ = positions[3*bIdx + 2]

					r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY) + (aZ - bZ)*(aZ - bZ)
					r = math.sqrt(r2)
					value += 1.0 * self.REPULSIVE / r
					
		return value

	def minimizedGradient(self, positions, pages, revPages, idxLangs, idxLinks, idxRedirects):
		gradient = numpy.array(len(positions) * [0.0])

		for aIdx, bIdx in idxLinks:
			aX = positions[3*aIdx + 0]
			aY = positions[3*aIdx + 1]
			aZ = positions[3*aIdx + 2]
			
			bX = positions[3*bIdx + 0]
			bY = positions[3*bIdx + 1]
			bZ = positions[3*bIdx + 2]
			
			r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY) + (aZ - bZ)*(aZ - bZ)
			r = math.sqrt(r2)
			weight = idxLinks[(aIdx, bIdx)]
			weight = weight * weight * weight
			
			gradient[3*aIdx + 0] += 2.0 * weight * (aX - bX) / r * (r - self.R)
			gradient[3*aIdx + 1] += 2.0 * weight * (aY - bY) / r * (r - self.R)
			gradient[3*aIdx + 2] += 2.0 * weight * (aZ - bZ) / r * (r - self.R)

			gradient[3*bIdx + 0] += 2.0 * weight * (bX - aX) / r * (r - self.R)
			gradient[3*bIdx + 1] += 2.0 * weight * (bY - aY) / r * (r - self.R)
			gradient[3*bIdx + 2] += 2.0 * weight * (bZ - aZ) / r * (r - self.R)
		
		for lang in idxLangs:
			for aIdx in idxLangs[lang]:
				for bIdx in idxLangs[lang]:
					if aIdx == bIdx:
						continue
					if idxRedirects[aIdx] == idxRedirects[bIdx]:
						continue
					aX = positions[3*aIdx + 0]
					aY = positions[3*aIdx + 1]
					aZ = positions[3*aIdx + 2]
			
					bX = positions[3*bIdx + 0]
					bY = positions[3*bIdx + 1]
					bZ = positions[3*bIdx + 2]

					r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY) + (aZ - bZ)*(aZ - bZ)
					r = math.sqrt(r2)
					r3 = r * r * r
					
					gradient[3*aIdx + 0] += self.REPULSIVE * (bX - aX) / r3
					gradient[3*aIdx + 1] += self.REPULSIVE * (bY - aY) / r3
					gradient[3*aIdx + 2] += self.REPULSIVE * (bZ - aZ) / r3

					gradient[3*bIdx + 0] += self.REPULSIVE * (aX - bX) / r3
					gradient[3*bIdx + 1] += self.REPULSIVE * (aY - bY) / r3
					gradient[3*bIdx + 2] += self.REPULSIVE * (aZ - bZ) / r3
		
		return gradient

	def processComponent(self, compKey):
		self.log.debug('Processing %s' % compKey)
		pages = self.dataRepository.getComponentPages(compKey)
		
		pageKeys = sorted(pages.keys())
		
		revPages = {}
		for idx in range(len(pageKeys)):
			page = pages[pageKeys[idx]]
			revPages[page['key']] = idx
		
		idxRedirects = len(pageKeys) * [-1]
		for idx in range(len(pageKeys)):
			page = pages[pageKeys[idx]]
			if page['redirect'] == None:
				idxRedirects[idx] = idx
			else:
				idxRedirects[idx] = revPages[page['redirect']]

		idxLangs = {}
		for idx in range(len(pages)):
			page = pages[pageKeys[idx]]
			if not page['lang'] in idxLangs:
				idxLangs[page['lang']] = []
			idxLangs[page['lang']] += [idx]
		
		idxLinks = {}
		links = self.dataRepository.getComponentLanglinks(compKey)
		for link in links:
			srcIdx, dstIdx = revPages[link[0]], revPages[link[1]]
			if srcIdx > dstIdx:
				srcIdx, dstIdx = dstIdx, srcIdx
			if (srcIdx, dstIdx) in idxLinks:
				idxLinks[(srcIdx, dstIdx)] += 1
			else:
				idxLinks[(srcIdx, dstIdx)] = 1
				idxLinks[(srcIdx, dstIdx)] += self.CATFACTOR * self.dataRepository.countCommonCategories(link[0], link[1])
				idxLinks[(srcIdx, dstIdx)] += self.LNKFACTOR * math.log(1.0 + self.dataRepository.countCommonLinks(link[0], link[1]))
			
		
		for pageKey in pageKeys:
			page = pages[pageKey]
			if page['redirect'] == None:
				continue
			srcIdx = revPages[page['key']]
			dstIdx = revPages[page['redirect']]
			idxLinks[(srcIdx, dstIdx)] = 1
		
		initialPositions = []
		for pageKey in pageKeys:
			initialPositions += [random.uniform(-self.INITBOX, self.INITBOX), random.uniform(-self.INITBOX, self.INITBOX), 0.0]

		finalPositions = initialPositions
		for _ in range(1):
			finalPositions = scipy.optimize.fmin_cg(self.minimizedFunction, finalPositions, self.minimizedGradient, args = (pages, revPages, idxLangs, idxLinks, idxRedirects), maxiter = 10000)
		pagePositions = {}
		for idx in range(len(pageKeys)):
			page = pages[pageKeys[idx]]
			pagePositions[page['key']] = (finalPositions[3*idx + 0], finalPositions[3*idx + 1], finalPositions[3*idx + 2])

		self.dataRepository.deletePagePositions(compKey)
		for pageKey in pageKeys:
			page = pages[pageKey]
			self.dataRepository.insertPagePosition(page['key'], compKey, pagePositions[page['key']])
	
	def doCalculate(self):
		self.dataRepository.connect()
		for compKey in self.dataRepository.getIncoherent():
			self.processComponent(compKey)
		self.dataRepository.disconnect()

class MeaningCalculator:
	AUTH = 'analysis'
	
	def __init__(self, dataRepository):
		self.log = logging.getLogger('MeaningCalculator')
		self.dataRepository = dataRepository

	def sqDist(self, src, dst):
		return 1.0 * (src[0] - dst[0])*(src[0] - dst[0]) + 1.0 * (src[1] - dst[1])*(src[1] - dst[1]) + 1.0 * (src[2] - dst[2])*(src[2] - dst[2])

	def cmpLinks(self, pagePositions, a, b):
		aDist = self.sqDist(pagePositions[a[0]], pagePositions[a[1]])
		bDist = self.sqDist(pagePositions[b[0]], pagePositions[b[1]])
		if aDist > bDist:
			return 1
		elif aDist < bDist:
			return -1
		else:
			return 0

	def mergeable(self, srcCluster, dstCluster, pages, clusters, langs):
		if srcCluster == dstCluster:
			return False
		srcLangSet = set(langs[srcCluster].keys())
		dstLangSet = set(langs[dstCluster].keys())
		commonLangs = srcLangSet & dstLangSet
		for commonLang in commonLangs:
			if langs[srcCluster][commonLang] != langs[dstCluster][commonLang]:
				return False
		return True
		
	def merge(self, srcCluster, dstCluster, pages, clusters, langs):
		for pageKey in pages:
			if clusters[pageKey] == dstCluster:
				clusters[pageKey] = srcCluster
				page = pages[pageKey]
				targetKey = pageKey
				if page['redirect'] != None:
					targetKey = page['redirect']
				langs[srcCluster][page['lang']] = targetKey
		del langs[dstCluster]

	def processComponent(self, compKey):
		self.log.debug('Processing %s' % compKey)
		pages = self.dataRepository.getComponentPages(compKey)
		pagePositions = self.dataRepository.getComponentPagePositions(compKey)
		links = self.dataRepository.getComponentLanglinks(compKey)
		for pageKey in pages:
			page = pages[pageKey]
			if page['redirect'] != None:
				links += [(page['key'], page['redirect'])]
		
		links.sort(lambda x, y: self.cmpLinks(pagePositions, x, y))
		
		clusters, langs = {}, {}
		idx = 0
		for pageKey in pages:
			page = pages[pageKey]
			targetKey = pageKey
			if page['redirect'] != None:
				targetKey = page['redirect']
			
			clusters[pageKey] = idx
			langs[idx] = {page['lang'] : targetKey}
			idx += 1

		for src, dst in links:
			if clusters[src] == clusters[dst]:
				continue
			if self.mergeable(clusters[src], clusters[dst], pages, clusters, langs):
				self.merge(clusters[src], clusters[dst], pages, clusters, langs)
		
		revClusters = {}
		for pageKey in pages:
			if not clusters[pageKey] in revClusters:
				revClusters[clusters[pageKey]] = [pageKey]
			else:
				revClusters[clusters[pageKey]] += [pageKey]
		
		self.dataRepository.deletePageMeanings(self.AUTH, compKey)
		for idx in revClusters:
			meaningPages = revClusters[idx]
			meaningKey = uuid.uuid5(uuid.NAMESPACE_URL, ' '.join(sorted(meaningPages)))
			self.dataRepository.insertPageMeanings(self.AUTH, str(meaningKey), compKey, meaningPages)


	def doCalculate(self):
		self.dataRepository.connect()
		for compKey in self.dataRepository.getIncoherent():
			self.processComponent(compKey)
		self.dataRepository.disconnect()

class ComponentDrawer:
	SCALE = 100.0
	AUTH = 'analysis'
	CATFACTOR = 0.8
	LNKFACTOR = 0.2

	def __init__(self, dataRepository, outputDir):
		self.log = logging.getLogger('ComponentDrawer')
		self.dataRepository = dataRepository
		self.outputDir = outputDir

	def map(self, position, offset):
		return (self.SCALE * (position[0] + offset[0]), self.SCALE * (position[1] + offset[1]))

	def draw(self, compKey):
		self.log.info('Visualizing ' + compKey)
		pagePositions = self.dataRepository.getComponentPagePositions(compKey)
		pages = self.dataRepository.getComponentPages(compKey)
		links = self.dataRepository.getComponentLanglinks(compKey)
		meanings = self.dataRepository.getComponentPageMeanings(compKey, self.AUTH)
		
		(minX, minY, maxX, maxY) = (sys.maxint, sys.maxint, -sys.maxint, -sys.maxint)  # FIXME
		for pageKey in pagePositions:
			position = pagePositions[pageKey]
			if (minX > position[0]):
				minX = position[0]
			if (maxX < position[0]):
				maxX = position[0]
			if (minY > position[1]):
				minY = position[1]
			if (maxY < position[1]):
				maxY = position[1]
		offset = (-minX, -minY)
		(width, height) = (maxX - minX, maxY - minY)

		weights = {}
		for aKey, bKey in links:
			if (bKey, aKey) in weights:
				continue
			weight = 0.4
			if (bKey, aKey) in links:
				weight += 0.4
			weight += self.CATFACTOR * self.dataRepository.countCommonCategories(aKey, bKey)
			weight += self.LNKFACTOR * math.log(1.0 + self.dataRepository.countCommonLinks(aKey, bKey))
			weights[(aKey, bKey)] = weight
		
		svg = ''
		svg += '<?xml version="1.0"?>\n'
		svg += '<svg height="%d" width="%d">\n' % (int(self.SCALE * height), int(self.SCALE * width))

		# Links
		svg += '<g style="stroke: lightgray;">\n'
		for aKey, bKey in weights:
			if meanings[aKey] != meanings[bKey]:
				continue
			weight = weights[(aKey, bKey)]
			aPos = self.map(pagePositions[aKey], offset)
			bPos = self.map(pagePositions[bKey], offset)
			svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
		svg += '</g>\n'
		
		# Links (cut)
		svg += '<g style="stroke: red;">\n'
		for aKey, bKey in weights:
			if meanings[aKey] == meanings[bKey]:
				continue
			weight = weights[(aKey, bKey)]
			aPos = self.map(pagePositions[aKey], offset)
			bPos = self.map(pagePositions[bKey], offset)
			svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
		svg += '</g>\n'
		
		# Redirects
		svg += '<g style="stroke: lightgray; stroke-width: 0.2;">\n'
		for pageKey in pagePositions:
			targetKey = pages[pageKey]['redirect']
			if targetKey == None:
				continue
			if meanings[pageKey] != meanings[targetKey]:
				continue
			aPos = self.map(pagePositions[pageKey], offset)
			bPos = self.map(pagePositions[targetKey], offset)
			svg += '  <line x1="%s" y1="%s" x2="%s" y2="%s"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1])
		svg += '</g>\n'

		# Redirects (cut)
		svg += '<g style="stroke: red; stroke-width: 0.2;">\n'
		for pageKey in pagePositions:
			targetKey = pages[pageKey]['redirect']
			if targetKey == None:
				continue
			if meanings[pageKey] == meanings[targetKey]:
				continue
			aPos = self.map(pagePositions[pageKey], offset)
			bPos = self.map(pagePositions[targetKey], offset)
			svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1])
		svg += '</g>\n'

		# Pages (circles)
		svg += '<g style="fill: lightgray; stroke: lightgray; stroke-width: 1;">\n'
		for pageKey in pagePositions:
			position = pagePositions[pageKey]
			page = pages[pageKey]

			mapped = self.map(position, offset)
			svg += '  <circle cx="%f" cy="%f" r="%f"/>\n' % (mapped[0], mapped[1], 1)
		svg += '</g>\n'

		# Pages (regular labels)
		svg += '<g style="stroke: black; stroke-width: 0.1; font-size: 4pt;">\n'
		for pageKey in pagePositions:
			position = pagePositions[pageKey]
			page = pages[pageKey]
			if page['redirect'] != None:
				continue
			
			ns = ''
			if page['namespace'] == 14:
				ns = 'Category:'

			mapped = self.map(position, offset)
			svg += '  <text x="%f" y="%f">%s</text>\n' % (mapped[0] + 1, mapped[1] + 1, page['lang'] + ':' + ns + page['title'])
		svg += '</g>\n'
		
		# Pages (redirect labels)
		svg += '<g style="stroke: black; stroke-width: 0.1; font-size: 2pt; font-style: italic;">\n'
		for pageKey in pagePositions:
			position = pagePositions[pageKey]
			page = pages[pageKey]
			if page['redirect'] == None:
				continue

			ns = ''
			if page['namespace'] == 14:
				ns = 'Category:'

			mapped = self.map(position, offset)
			svg += '  <text x="%f" y="%f">%s</text>\n' % (mapped[0] + 1, mapped[1] + 1, page['lang'] + ':' + ns + page['title'])
		svg += '</g>\n'

		svg += '</svg>\n'
		
		file = open(self.outputDir + os.sep + compKey + '.svg', 'w')
		file.write(svg)
		file.close()
		
	def doDraw(self):
		self.dataRepository.connect()
		for compKey in self.dataRepository.getIncoherent():
			self.draw(compKey)
		self.dataRepository.disconnect()
