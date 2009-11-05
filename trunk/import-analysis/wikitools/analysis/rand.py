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

class RandomMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'random'
    AUTH = 'analysis.random'
    
    REPEAT = 10
    
    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('RandomMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

    def doProcess(self, comp):
        min, max, sum = sys.maxint, -1, 0
        for _ in xrange(self.REPEAT):
            cost = self.go(comp)
            if min > cost:
                min = cost
            if max < cost:
                max = cost
            sum += cost
        avg = sum / self.REPEAT
        
        self.log.info('Min. cost: %s %d' % (comp.key, min))
        self.log.info('Avg. cost: %s %d' % (comp.key, avg))
        self.log.info('Max. cost: %s %d' % (comp.key, max))

    def go(self, comp):
        links = []
        for link in comp.mLinks:
            links += [link]
        random.shuffle(links)

        cost = 0
        comp.initClusters()
        for src, dst in links:
            if comp.mergeable(comp.clusters[src], comp.clusters[dst]):
                comp.merge(comp.clusters[src], comp.clusters[dst])
            elif comp.clusters[src] != comp.clusters[dst]:
                cost += comp.weights[(src, dst)]

        return cost
