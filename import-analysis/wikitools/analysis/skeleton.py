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

import logging, math, numpy, os, random, scipy.optimize, sys, uuid, wikitools.analysis.common

class SkeletonPainter(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'visualize'
    SCALE = 12.0
    AUTH = 'analysis.genetic'
    WIDTH = 0.4

    REPULSIVE = 40.0
    INITBOX = 100.0
    MAXITER = 120
    R = 2.0

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('SkeletonPainter')
        self.dataRepository = dataRepository
        self.options = options

    def map(self, position, offset):
        return (self.SCALE * (position[0] + offset[0]), self.SCALE * (position[1] + offset[1]))

    def doProcess(self, comp):
        compKey = comp.key
        meanings = self.dataRepository.getComponentPageMeanings(compKey, self.AUTH)

        meaningKeys = sorted(set(meanings.values()))
        revMeanings = {}
        for idx in range(len(meaningKeys)):
            revMeanings[meaningKeys[idx]] = idx
        
        meaningSizes = {}
        meaningLabels = {}
        for meaningKey in meaningKeys:
            meaningSizes[meaningKey] = 0
            meaningLabels[meaningKey] = ''
        for pageKey in comp.mPages:
            meaningKey = meanings[pageKey]
            meaningSizes[meaningKey] += 1
            if comp.pages[pageKey]['lang'] == 'en':
                meaningLabels[meaningKey] = comp.pages[pageKey]['title']
        
        links = {}
        for (aKey, bKey) in comp.mLinks:
            aMeaningKey, bMeaningKey = meanings[aKey], meanings[bKey]
            if aMeaningKey == bMeaningKey:
                continue
            if aMeaningKey > bMeaningKey:
                aMeaningKey, bMeaningKey = bMeaningKey, aMeaningKey
            if not (aMeaningKey, bMeaningKey) in links:
                links[(aMeaningKey, bMeaningKey)] = 0
            links[(aMeaningKey, bMeaningKey)] += 1

        idxLinks = {}
        for link in links:
            srcIdx, dstIdx = revMeanings[link[0]], revMeanings[link[1]]
            if srcIdx > dstIdx:
                srcIdx, dstIdx = dstIdx, srcIdx
            idxLinks[(srcIdx, dstIdx)] = links[link]

        initialPositions = []
        for meaningKey in meaningKeys:
            initialPositions += [random.uniform(-self.INITBOX, self.INITBOX), random.uniform(-self.INITBOX, self.INITBOX)]
        finalPositions = scipy.optimize.fmin_cg(self.minimizedFunction, initialPositions, self.minimizedGradient, args = (idxLinks,), maxiter = self.MAXITER)

        meaningPos = {}
        for idx in range(len(meaningKeys)):
            meaningPos[meaningKeys[idx]] = (finalPositions[2*idx + 0], finalPositions[2*idx + 1])


        (minX, minY, maxX, maxY) = (sys.maxint, sys.maxint, -sys.maxint, -sys.maxint)  # FIXME
        for meaningKey in meaningPos:
            position = meaningPos[meaningKey]
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

        svg = ''
        svg += '<?xml version="1.0"?>\n'
        svg += '<svg height="%d" width="%d">\n' % (int(self.SCALE * height), int(self.SCALE * width))

        # Links (cut)
        svg += '<g style="stroke: red;">\n'
        for aKey, bKey in links:
            aPos = self.map(meaningPos[aKey], offset)
            bPos = self.map(meaningPos[bKey], offset)
            weight = self.WIDTH * math.log(1.0 + links[(aKey, bKey)])
            svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
        svg += '</g>\n'

        # Meanings (circles)
        svg += '<g style="fill: lightgray; stroke: lightgray; stroke-width: 1;">\n'
        for meaningKey in meaningPos:
            position = meaningPos[meaningKey]

            mapped = self.map(position, offset)
            radius = math.sqrt(meaningSizes[meaningKey])
            svg += '  <circle cx="%f" cy="%f" r="%f"/>\n' % (mapped[0], mapped[1], radius)
        svg += '</g>\n'

        # Pages (regular labels)
        svg += '<g style="stroke: black; stroke-width: 0.1; font-size: 4pt;">\n'
        for meaningKey in meaningPos:
            position = meaningPos[meaningKey]
            
            mapped = self.map(position, offset)
            svg += '  <text x="%f" y="%f">%s</text>\n' % (mapped[0] - 1, mapped[1] - 1, meaningLabels[meaningKey])
        svg += '</g>\n'
        
        svg += '</svg>\n'
        
        path = self.options.outputDir + os.sep + compKey[0:2] + os.sep + compKey[2:4]
        if not os.path.isdir(path):
            os.makedirs(path)
        file = open(path + os.sep + compKey + '.skel.svg', 'w')
        file.write(svg)
        file.close()

    def minimizedFunction(self, positions, idxLinks):
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

        n = len(positions) / 2
        for aIdx in xrange(n):
            for bIdx in xrange(aIdx):
                aX = positions[2*aIdx + 0]
                aY = positions[2*aIdx + 1]
                bX = positions[2*bIdx + 0]
                bY = positions[2*bIdx + 1]

                r2 = (aX - bX)*(aX - bX) + (aY - bY)*(aY - bY)
                r = math.sqrt(r2)
                value += 1.0 * self.REPULSIVE / r

        return value


    def minimizedGradient(self, positions, idxLinks):
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

        n = len(positions) / 2
        for aIdx in xrange(n):
            for bIdx in xrange(aIdx):
                aX = positions[2*aIdx + 0]
                aY = positions[2*aIdx + 1]
                bX = positions[2*bIdx + 0]
                bY = positions[2*bIdx + 1]

                abX = aX - bX
                abY = aY - bY

                r2 = abX**2 + abY**2
                r = math.sqrt(r2)
                r3 = r * r * r
                
                tmp = 1.0 * self.REPULSIVE / r3
                tmpX, tmpY = tmp * abX, tmp * abY
                gradient[2*aIdx + 0] -= tmpX
                gradient[2*aIdx + 1] -= tmpY
                gradient[2*bIdx + 0] += tmpX
                gradient[2*bIdx + 1] += tmpY

        return gradient





class LazySkeletonPainter(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'visualize'
    SCALE = 10.0
    AUTH = 'analysis.genetic'
    WIDTH = 0.4

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('LazySkeletonPainter')
        self.dataRepository = dataRepository
        self.options = options

    def map(self, position, offset):
        return (self.SCALE * (position[0] + offset[0]), self.SCALE * (position[1] + offset[1]))

    def doProcess(self, comp):
        compKey = comp.key
        pagePositions = self.dataRepository.getComponentPagePositions(compKey)
        meanings = self.dataRepository.getComponentPageMeanings(compKey, self.AUTH)
        
        meaningKeys = set(meanings.values())
        meaningPos = {}
        meaningSizes = {}
        meaningLabels = {}
        for meaningKey in meaningKeys:
            meaningPos[meaningKey] = [0, 0]
            meaningSizes[meaningKey] = 0
            meaningLabels[meaningKey] = ''
        for pageKey in comp.mPages:
            position = pagePositions[pageKey]
            meaningKey = meanings[pageKey]
            meaningPos[meaningKey][0] += position[0]
            meaningPos[meaningKey][1] += position[1]
            meaningSizes[meaningKey] += 1
            if comp.pages[pageKey]['lang'] == 'en':
                meaningLabels[meaningKey] = comp.pages[pageKey]['title']
        for meaningKey in meaningKeys:
            meaningPos[meaningKey][0] /= meaningSizes[meaningKey]
            meaningPos[meaningKey][1] /= meaningSizes[meaningKey]
        
        links = {}
        for (aKey, bKey) in comp.mLinks:
            aMeaningKey, bMeaningKey = meanings[aKey], meanings[bKey]
            if aMeaningKey > bMeaningKey:
                aMeaningKey, bMeaningKey = bMeaningKey, aMeaningKey
            if not (aMeaningKey, bMeaningKey) in links:
                links[(aMeaningKey, bMeaningKey)] = 0
            links[(aMeaningKey, bMeaningKey)] += 1


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

        svg = ''
        svg += '<?xml version="1.0"?>\n'
        svg += '<svg height="%d" width="%d">\n' % (int(self.SCALE * height), int(self.SCALE * width))

        # Links (cut)
        svg += '<g style="stroke: red;">\n'
        for aKey, bKey in links:
            aPos = self.map(meaningPos[aKey], offset)
            bPos = self.map(meaningPos[bKey], offset)
            weight = self.WIDTH * math.log(1.0 + links[(aKey, bKey)])
            svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
        svg += '</g>\n'

        # Meanings (circles)
        svg += '<g style="fill: lightgray; stroke: lightgray; stroke-width: 1;">\n'
        for meaningKey in meaningPos:
            position = meaningPos[meaningKey]

            mapped = self.map(position, offset)
            radius = math.sqrt(meaningSizes[meaningKey])
            svg += '  <circle cx="%f" cy="%f" r="%f"/>\n' % (mapped[0], mapped[1], radius)
        svg += '</g>\n'

        # Pages (regular labels)
        svg += '<g style="stroke: black; stroke-width: 0.1; font-size: 4pt;">\n'
        for meaningKey in meaningPos:
            position = meaningPos[meaningKey]
            
            mapped = self.map(position, offset)
            svg += '  <text x="%f" y="%f">%s</text>\n' % (mapped[0] - 1, mapped[1] - 1, meaningLabels[meaningKey])
        svg += '</g>\n'
        
        svg += '</svg>\n'
        
        path = self.options.outputDir + os.sep + compKey[0:2] + os.sep + compKey[2:4]
        if not os.path.isdir(path):
            os.makedirs(path)
        file = open(path + os.sep + compKey + '.skel.svg', 'w')
        file.write(svg)
        file.close()
