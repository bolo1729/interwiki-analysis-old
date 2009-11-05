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

class Cluster:
    def __init__(self, comp):
        self.comp = comp
        self.pages = set()
        self.langs = set()
        self.weights = {}
        self.sum = 0
    
    def addWeight(self, cj, w):
        if not cj in self.weights:
            self.weights[cj] = 0
        self.weights[cj] += w

class CliquesMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'cliques'
    AUTH = 'analysis.cliques'
    
    THETA = 5
    
    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('CliquesMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

    def findHeaviest(self, lookup, _, possible, langs):
        max, arg = -1, None
        for ci in possible:
            if langs & lookup[ci].langs != set():
                continue
            w = lookup[ci].sum
            if max < w:
                max, arg = w, ci
        # self.log.debug('Heaviest: ' + str(arg))
        return arg

    def findClosest(self, lookup, group, possible, langs):
        max, arg = -1, None
        for ci in possible:
            if langs & lookup[ci].langs != set():
                continue
            w = 0
            for cj in lookup[ci].weights:
                if cj in group:
                    w += lookup[ci].weights[cj]
            if max < w:
                max, arg = w, ci
        # self.log.debug('Closest: ' + str(arg))
        return arg

    def doProcess(self, comp):
        lookup = {}

        for pageKey in comp.mPages:
            ci = comp.clusters[pageKey]
            if ci in lookup:
                raise Exception, 'Someone touched my clusters!'
            lookup[ci] = Cluster(comp)
            lookup[ci].pages = set([pageKey])
            lookup[ci].langs = set([comp.pages[pageKey]['lang']])

        self.updateLookup(comp, lookup)
        
        self.go(comp, lookup, self.THETA, self.findHeaviest)
        self.go(comp, lookup, 2, self.findClosest)

        cost = 0
        for src, dst in comp.mLinks:
            if comp.clusters[src] != comp.clusters[dst]:
                cost += comp.weights[(src, dst)]

        self.log.info('Total cost: %s %d' % (comp.key, cost))
        
        self.storeMeaning(comp)

    def go(self, comp, lookup, theta, func):
        failed = set()
        while True:
            # self.log.debug('Lookup: ' + str(map(lambda x: str(x) + ":" + str(lookup[x].pages), lookup)))
            group = set()
            langs = set()
            possible = set(lookup.keys()) - failed
            start = self.findHeaviest(lookup, None, possible, langs)
            if start == None:
                break
            current = start
            while current != None:
                group |= set([current])
                langs |= lookup[current].langs
                possible &= set(lookup[current].weights.keys())
                current = func(lookup, group, possible, langs)
            
            if len(group) < theta:
                failed |= set([start])
            else:
                self.merge(group, comp, lookup)

    def updateLookup(self, comp, lookup):
        for ci in lookup:
            lookup[ci].weights = {}

        for (fromKey, toKey) in comp.mLinks:
            ciFrom = comp.clusters[fromKey]
            ciTo = comp.clusters[toKey]
            w = comp.weights[(fromKey, toKey)]
            lookup[ciFrom].addWeight(ciTo, w)
            lookup[ciTo].addWeight(ciFrom, w)

        for ci in lookup:
            cluster = lookup[ci]
            sum = 0
            for cj in lookup[ci].weights:
                sum += lookup[ci].weights[cj]
            lookup[ci].sum = sum

    def merge(self, group, comp, lookup):
        # self.log.debug('Merging ' + str(map(lambda x: lookup[x].pages, group)))
        if len(group) < 2:
            return

        group = map(None, group)
        master, rest = group[0], group[1:]
        for cj in rest:
            lookup[master].pages |= lookup[cj].pages
            lookup[master].langs |= lookup[cj].langs
            comp.merge(master, cj)
            del lookup[cj]
        self.updateLookup(comp, lookup)
