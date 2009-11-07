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

class NewmanGirvanMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'newman-girvan'
    AUTH = 'analysis.newman-girvan'

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('NewmanGirvanMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options
        self.bmc = BetweennessMeaningCalculator(dataRepository, options)

    def checkCut(self, comp, cut):
        comp.setCut(cut, True)
        comp.langs = {}
        badClusters = set()
        for pageKey in comp.mPages:
            lang = comp.pages[pageKey]['lang']
            ci = comp.clusters[pageKey]
            if not ci in comp.langs:
                comp.langs[ci] = set()
            if lang in comp.langs[ci]:
                badClusters |= set([ci])
            comp.langs[ci] |= set([lang])
        badPages = set()
        for pageKey in comp.mPages:
            if comp.clusters[pageKey] in badClusters:
                badPages |= set([pageKey])
        return badPages

    def doProcess(self, comp):
        ignored = set()
        scope = comp.mPages
        sequence = []
        while len(sequence) < len(comp.mLinks):
            eb = self.bmc.edgeBetweenness(comp, ignored, scope)
            last = eb[-1]
            ignored |= set([last])
            sequence += [last]
            scope = self.checkCut(comp, ignored)
            self.log.debug('Got %s, new scope size: %d' % (last,len(scope)))
            if scope == set():
                break

        cost = 0
        for (src, dst) in sequence:
            if comp.mergeable(comp.clusters[src], comp.clusters[dst]):
                comp.merge(comp.clusters[src], comp.clusters[dst])
            elif comp.clusters[src] != comp.clusters[dst]:
                cost += comp.weights[(src, dst)]

        self.log.info('Total cost: %s %d' % (comp.key, cost))

        self.storeMeaning(comp)

class BetweennessMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'betweenness'
    AUTH = 'analysis.betweenness'

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('BetweennessMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

    def doProcess(self, comp):
        links = self.edgeBetweenness(comp, set())

        cost = 0
        comp.initClusters()
        for src, dst in links:
            if comp.mergeable(comp.clusters[src], comp.clusters[dst]):
                comp.merge(comp.clusters[src], comp.clusters[dst])
            elif comp.clusters[src] != comp.clusters[dst]:
                cost += comp.weights[(src, dst)]

        self.log.info('Total cost: %s %d' % (comp.key, cost))

        self.storeMeaning(comp)

    def edgeBetweenness(self, comp, ignored = None, scope = None):
        total = {}
        neighbors = {}
        for (src, dst) in comp.mLinks:
            if (src, dst) in ignored:
                continue
            total[(src, dst)] = 0.0
            if src in neighbors:
                neighbors[src] |= set([dst])
            else:
                neighbors[src] = set([dst])
            if dst in neighbors:
                neighbors[dst] |= set([src])
            else:
                neighbors[dst] = set([src])

        if scope == None:
            scope = comp.mPages

        for pageKey in scope:
            self.processSingleSource(pageKey, total, comp, neighbors, ignored)

        sortedLinks = sorted(total.keys(), lambda x, y: cmp(total[x], total[y]))
        # self.log.debug('Edge betweenness: ' + str(map(lambda x : (x, total[x]), sortedLinks)))
        return sortedLinks

    def processSingleSource(self, startKey, total, comp, neighbors, ignored):
        d, w, nexts, prevs = {}, {}, {}, {}
        queue = [startKey]
        d[startKey] = 0
        w[startKey] = 1.0
        prevs[startKey] = set()
        sequence = [startKey]
        while len(queue) > 0:
            curKey, queue = queue[0], queue[1:]
            nexts[curKey] = set()
            dcur, wcur = d[curKey], w[curKey]
            if not curKey in neighbors:
                continue
            for nextKey in neighbors[curKey]:
                a, b = min(curKey, nextKey), max(curKey, nextKey)
                if (a, b) in ignored:
                    continue
                if not nextKey in d:
                    queue += [nextKey]
                    d[nextKey] = dcur + 1
                    w[nextKey] = wcur
                    prevs[nextKey] = set([curKey])
                    sequence += [nextKey]
                    nexts[curKey] |= set([nextKey])
                elif d[nextKey] == dcur + 1:
                    w[nextKey] += wcur
                    prevs[nextKey] |= set([curKey])
                    nexts[curKey] |= set([nextKey])
                    
        # self.log.debug('Sequence: ' + str(sequence))
        eb = {}
        dmax = max(d.values())
        for curKey in reversed(sequence):
            dcur, wcur = d[curKey], w[curKey]

            sum = 1.0
            for nextKey in nexts[curKey]:
                a, b = min(curKey, nextKey), max(curKey, nextKey)
                sum += eb[(a, b)]

            for prevKey in prevs[curKey]:
                aa, bb = min(prevKey, curKey), max(prevKey, curKey)
                eb[(aa, bb)] = sum * w[prevKey] / wcur

        # sortedEB = sorted(eb.keys(), lambda x, y: cmp(eb[x], eb[y]))
        # self.log.debug('EB for ' + startKey + ': ' + str(map(lambda x : (x, eb[x]), sortedEB)))

        for (a, b) in eb:
            total[(a, b)] += eb[(a, b)]
