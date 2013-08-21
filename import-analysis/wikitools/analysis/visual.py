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

import logging, math, os, random, sys, uuid, wikitools.analysis.common

class ComponentPainter(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'visualize'
    SCALE = 100.0
    AUTH = 'analysis.genetic'
    WIDTH = 0.4

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('ComponentDrawer')
        self.dataRepository = dataRepository
        self.options = options

    def map(self, position, offset):
        return (self.SCALE * (position[0] + offset[0]), self.SCALE * (position[1] + offset[1]))

    def doProcess(self, comp):
        compKey = comp.key
        pages = comp.pages
        links = comp.links
        pagePositions = self.dataRepository.getComponentPagePositions(compKey)
        meanings = self.dataRepository.getComponentPageMeanings(compKey, self.AUTH)
        
        links = set(links)
        rlinks = set([])
        for (aKey, bKey) in links:
            target = pages[bKey]['redirect']
            if target == None:
                rlinks |= set([(aKey, bKey)])
            else:
                rlinks |= set([(aKey, target)])
        
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

        # Links
        svg += '<g style="stroke: lightgray;">\n'
        for aKey, bKey in comp.weights:
            if meanings[aKey] != meanings[bKey]:
                continue
            weight = self.WIDTH * comp.weights[(aKey, bKey)]
            aPos = self.map(pagePositions[aKey], offset)
            bPos = self.map(pagePositions[bKey], offset)
            svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
        svg += '</g>\n'
        
        # Links (cut)
        svg += '<g style="stroke: red;">\n'
        for aKey, bKey in comp.weights:
            if meanings[aKey] == meanings[bKey]:
                continue
            weight = self.WIDTH * comp.weights[(aKey, bKey)]
            aPos = self.map(pagePositions[aKey], offset)
            bPos = self.map(pagePositions[bKey], offset)
            svg += '  <line x1="%f" y1="%f" x2="%s" y2="%s" style="stroke-width: %s;"/>\n' % (aPos[0], aPos[1], bPos[0], bPos[1], weight)
        svg += '</g>\n'

        # Pages (circles)
        svg += '<g style="fill: lightgray; stroke: lightgray; stroke-width: 1;">\n'
        for pageKey in pagePositions:
            if pages[pageKey]['redirect'] != None:
                continue
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
        
        svg += '</svg>\n'
        
        path = self.options.outputDir + os.sep + compKey[0:2] + os.sep + compKey[2:4]
        if not os.path.isdir(path):
            os.makedirs(path)
        file = open(path + os.sep + compKey + '.svg', 'w')
        file.write(svg)
        file.close()
