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
	INITBOX = 10.0
	R = 1.0
	S = 10.0
	REPULSIVE = 10.0

	def __init__(self, dataRepository, options):
		self.log = logging.getLogger('PagePositionCalculator')
		self.dataRepository = dataRepository
		self.options = options

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

		idxLinks = {}
		for link in comp.mLinks:
			srcIdx, dstIdx = revPages[link[0]], revPages[link[1]]
			if srcIdx > dstIdx:
				srcIdx, dstIdx = dstIdx, srcIdx
			idxLinks[(srcIdx, dstIdx)] = comp.weights[link]

		initialPositions = []
		for pageKey in pageKeys:
			initialPositions += [random.uniform(-self.INITBOX, self.INITBOX), random.uniform(-self.INITBOX, self.INITBOX)]

		finalPositions = initialPositions
		for _ in range(1):
			finalPositions = scipy.optimize.fmin_cg(self.minimizedFunction, finalPositions, self.minimizedGradient, args = (comp.pages, revPages, idxLangs, idxLinks))
		pagePositions = {}
		for idx in range(len(pageKeys)):
			pagePositions[pageKeys[idx]] = (finalPositions[2*idx + 0], finalPositions[2*idx + 1])

		self.dataRepository.deletePagePositions(comp.key)
		for pageKey in pageKeys:
			pos = pagePositions[pageKey]
			self.dataRepository.insertPagePosition(pageKey, comp.key, (pos[0], pos[1], 0.0))

	def minimizedFunction(self, positions, pages, revPages, idxLangs, idxLinks):
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

		for lang in idxLangs:
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
					# value += 1.0 * self.REPULSIVE / r
					value += 1.0 * self.REPULSIVE * (r - self.S) * (r - self.S)
					
		return value

	def minimizedGradient(self, positions, pages, revPages, idxLangs, idxLinks):
		gradient = numpy.array(len(positions) * [0.0])

		for aIdx, bIdx in idxLinks:
			aX = positions[2*aIdx + 0]
			aY = positions[2*aIdx + 1]
			
			bX = positions[2*bIdx + 0]
			bY = positions[2*bIdx + 1]
			
			r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY)
			r = math.sqrt(r2)
			weight = idxLinks[(aIdx, bIdx)]

			gradient[2*aIdx + 0] += 2.0 * weight * (aX - bX) / r * (r - self.R)
			gradient[2*aIdx + 1] += 2.0 * weight * (aY - bY) / r * (r - self.R)

			gradient[2*bIdx + 0] += 2.0 * weight * (bX - aX) / r * (r - self.R)
			gradient[2*bIdx + 1] += 2.0 * weight * (bY - aY) / r * (r - self.R)

		for lang in idxLangs:
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
					r3 = r * r * r
					
					# gradient[2*aIdx + 0] += self.REPULSIVE * (bX - aX) / r3
					# gradient[2*aIdx + 1] += self.REPULSIVE * (bY - aY) / r3

					# gradient[2*bIdx + 0] += self.REPULSIVE * (aX - bX) / r3
					# gradient[2*bIdx + 1] += self.REPULSIVE * (aY - bY) / r3

					gradient[2*aIdx + 0] += 2.0 * self.REPULSIVE * (aX - bX) / r * (r - self.S)
					gradient[2*aIdx + 1] += 2.0 * self.REPULSIVE * (aY - bY) / r * (r - self.S)

					gradient[2*bIdx + 0] += 2.0 * self.REPULSIVE * (bX - aX) / r * (r - self.S)
					gradient[2*bIdx + 1] += 2.0 * self.REPULSIVE * (bY - aY) / r * (r - self.S)

		return gradient
