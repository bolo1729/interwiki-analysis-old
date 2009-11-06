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

import logging, math, numpy, random, scipy.optimize, wikitools.analysis.common

class PagePositionCalculator(wikitools.analysis.common.AbstractComponentProcessor):
	NAME = 'positions'
	
	INITBOX = 100.0
	R = 1.0
	S = 10.0
	REPULSIVE = 40.0

	MAXITER = 100
	FASTLANGS = 3
	BOOST = 10.0

	def __init__(self, dataRepository, options):
		self.log = logging.getLogger('PagePositionCalculator')
		self.dataRepository = dataRepository
		self.options = options
		self.altPotential = 'alt-potential' in self.options.switches
		self.fastPos = 'fast-pos' in self.options.switches
		self.timing = 'timing' in self.options.switches

	def doProcess(self, comp):
		pageKeys = sorted(comp.mPages)

		revPages = {}
		for idx in range(len(pageKeys)):
			revPages[pageKeys[idx]] = idx

		idxLangs = {}
		for idx in range(len(comp.mPages)):
			page = comp.pages[pageKeys[idx]]
			if not page['lang'] in idxLangs:
				idxLangs[page['lang']] = set()
			idxLangs[page['lang']] |= set([idx])

		mainLangs = idxLangs.keys()
		if self.fastPos and len(mainLangs) > self.FASTLANGS:
			langFreqs = map(lambda l : (len(idxLangs[l]), l), idxLangs)
			langFreqs.sort()
			langFreqs.reverse()
			mainLangs = map(lambda p : p[1], langFreqs)
			mainLangs = mainLangs[0:self.FASTLANGS]

		idxLinks = {}
		for link in comp.mLinks:
			srcIdx, dstIdx = revPages[link[0]], revPages[link[1]]
			if srcIdx > dstIdx:
				srcIdx, dstIdx = dstIdx, srcIdx
			idxLinks[(srcIdx, dstIdx)] = comp.weights[link]

		initialPositions = []
		for pageKey in pageKeys:
			initialPositions += [random.uniform(-self.INITBOX, self.INITBOX), random.uniform(-self.INITBOX, self.INITBOX)]

		if self.timing:
			import time
			repeat = 50

			ts = time.time()
			for _ in xrange(repeat):
				self.minimizedFunction(initialPositions, comp.pages, revPages, idxLangs, idxLinks, mainLangs)
			te = time.time()
			self.log.debug('Function: %8.5f ms' % (1000.0*(te - ts)/repeat))

			ts = time.time()
			for _ in xrange(repeat):
				self.minimizedGradient(initialPositions, comp.pages, revPages, idxLangs, idxLinks, mainLangs)
			te = time.time()
			self.log.debug('Gradient: %8.5f ms' % (1000.0*(te - ts)/repeat))

		finalPositions = initialPositions
		if self.fastPost:
			finalPositions = scipy.optimize.fmin_cg(self.minimizedFunction, finalPositions, self.minimizedGradient, args = (comp.pages, revPages, idxLangs, idxLinks, mainLangs), maxiter = self.MAXITER)
		else:
			finalPositions = scipy.optimize.fmin_cg(self.minimizedFunction, finalPositions, self.minimizedGradient, args = (comp.pages, revPages, idxLangs, idxLinks, mainLangs))

		pagePositions = {}
		for idx in range(len(pageKeys)):
			pagePositions[pageKeys[idx]] = (finalPositions[2*idx + 0], finalPositions[2*idx + 1])

		self.dataRepository.deletePagePositions(comp.key)
		for pageKey in pageKeys:
			pos = pagePositions[pageKey]
			self.dataRepository.insertPagePosition(pageKey, comp.key, (pos[0], pos[1], 0.0))

	def minimizedFunction(self, positions, pages, revPages, idxLangs, idxLinks, mainLangs):
		value = 0.0
		for aIdx, bIdx in idxLinks:
			aX = positions[2*aIdx + 0]
			aY = positions[2*aIdx + 1]
			bX = positions[2*bIdx + 0]
			bY = positions[2*bIdx + 1]
			
			r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY)
			r = math.sqrt(r2)
			weight = idxLinks[(aIdx, bIdx)]
			value += weight * (r - self.R) * (r - self.R)

		boost = 1.0
		if self.fastPos:
			boost = self.BOOST

		for lang in mainLangs:
			for aIdx in idxLangs[lang]:
				for bIdx in idxLangs[lang]:
					if aIdx == bIdx:
						continue
					aX = positions[2*aIdx + 0]
					aY = positions[2*aIdx + 1]
					bX = positions[2*bIdx + 0]
					bY = positions[2*bIdx + 1]

					r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY)
					r = math.sqrt(r2)
					if self.altPotential:
						value += 1.0 * boost * self.REPULSIVE * (r - self.S) * (r - self.S)
					else:
						value += 1.0 * boost * self.REPULSIVE / r

		return value


	def minimizedGradient(self, positions, pages, revPages, idxLangs, idxLinks, mainLangs):
		gradient = numpy.array(len(positions) * [0.0])
		
		for aIdx, bIdx in idxLinks:
			aX = positions[2*aIdx + 0]
			aY = positions[2*aIdx + 1]
			bX = positions[2*bIdx + 0]
			bY = positions[2*bIdx + 1]

			abX = aX - bX
			abY = aY - bY

			r2 = abX**2 + abY**2
			r = math.sqrt(r2)
			weight = idxLinks[(aIdx, bIdx)]

			tmp = 2.0 * weight / r * (r - self.R)
			tmpX, tmpY = tmp * abX, tmp * abY
			gradient[2*aIdx + 0] += tmpX
			gradient[2*aIdx + 1] += tmpY
			gradient[2*bIdx + 0] -= tmpX
			gradient[2*bIdx + 1] -= tmpY

		boost = 1.0
		if self.fastPos:
			boost = self.BOOST

		for lang in mainLangs:
			for aIdx in idxLangs[lang]:
				for bIdx in idxLangs[lang]:
					if aIdx == bIdx:
						continue
					aX = positions[2*aIdx + 0]
					aY = positions[2*aIdx + 1]
					bX = positions[2*bIdx + 0]
					bY = positions[2*bIdx + 1]

					abX = aX - bX
					abY = aY - bY

					r2 = abX**2 + abY**2
					r = math.sqrt(r2)
					r3 = r * r * r
					
					if self.altPotential:
						gradient[2*aIdx + 0] += 2.0 * boost * self.REPULSIVE * (aX - bX) / r * (r - self.S)
						gradient[2*aIdx + 1] += 2.0 * boost * self.REPULSIVE * (aY - bY) / r * (r - self.S)
						gradient[2*bIdx + 0] += 2.0 * boost * self.REPULSIVE * (bX - aX) / r * (r - self.S)
						gradient[2*bIdx + 1] += 2.0 * boost * self.REPULSIVE * (bY - aY) / r * (r - self.S)
					else:
						tmp = 1.0 * boost * self.REPULSIVE / r3
						tmpX, tmpY = tmp * abX, tmp * abY
						gradient[2*aIdx + 0] -= tmpX
						gradient[2*aIdx + 1] -= tmpY
						gradient[2*bIdx + 0] += tmpX
						gradient[2*bIdx + 1] += tmpY

		return gradient
