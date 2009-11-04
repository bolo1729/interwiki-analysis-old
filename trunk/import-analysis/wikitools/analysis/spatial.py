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

class SpatialMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    AUTH = 'analysis.spatial'
    
    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('SpatialMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

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

    def doProcess(self, comp):
        pagePositions = self.dataRepository.getComponentPagePositions(comp.key)
        
        links = []
        for link in comp.mLinks:
            links += [link]
        links.sort(lambda x, y: self.cmpLinks(pagePositions, x, y))

        comp.initClusters()
        for src, dst in links:
            if comp.mergeable(comp.clusters[src], comp.clusters[dst]):
                comp.merge(comp.clusters[src], comp.clusters[dst])
        
        self.storeMeaning(comp)
