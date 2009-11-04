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

import logging, math, random, uuid

class Component:
    def __init__(self, key, pages, links):
        self.key = key
        self.pages = pages
        self.links = links

        self.mPages = set()
        for pageKey in self.pages:
            if self.pages[pageKey]['redirect'] == None:
                self.mPages |= set([pageKey])
        self.mPages = frozenset(self.mPages)

        self.mLinks = set()
        for (fromKey, toKey) in self.links:
            target = pages[toKey]['redirect']
            if target != None:
                toKey = target
            if fromKey > toKey:
                (fromKey, toKey) = (toKey, fromKey)
            self.mLinks |= set([(fromKey, toKey)])
        self.mLinks = frozenset(self.mLinks)

        self.initClusters()
        self.updateWeights()

        self.cut = set()

    def initClusters(self):
        self.clusters, self.langs, ci = {}, {}, 0
        for pageKey in self.mPages:
            page = self.pages[pageKey]
            self.clusters[pageKey] = ci
            self.langs[ci] = set([page['lang']])
            ci += 1

    def mergeable(self, ca, cb):
        if ca == cb:
            return False
        return self.langs[ca] & self.langs[cb] == set()

    def merge(self, ca, cb):
        if ca == cb:
            return
        if self.langs[ca] & self.langs[cb] != set():
            raise Exception, 'Incoherent cluster after merge'
        for pageKey in self.mPages:
            if self.clusters[pageKey] == cb:
                self.clusters[pageKey] = ca
        self.langs[ca] |= self.langs[cb]
        del self.langs[cb]
    
    def setCut(self, cut):
        self.cut = cut

        self.clusters, self.langs, ci = {}, {}, 0
        for pageKey in self.mPages:
            page = self.pages[pageKey]
            self.clusters[pageKey] = ci
            self.langs[ci] = set([page['lang']])
            ci += 1

        for (fromKey, toKey) in self.mLinks:
            if not (fromKey, toKey) in self.cut:
                self.merge(self.clusters[fromKey], self.clusters[toKey])

    WEIGHT_NORMAL = 1.0
    WEIGHT_REDIRECT = 0.1
    FACTOR_CATEGORY = 0.8
    FACTOR_LINK = 0.2

    def updateWeights(self, repository = None, commonCategories = False, commonLinks = False):
        self.weights = {}
        self.commonCategories = {}
        self.commonLinks = {}
        for (fromKey, toKey) in self.links:
            target = self.pages[toKey]['redirect']
            if target != None:
                toKey = target
            if fromKey > toKey:
                (fromKey, toKey) = (toKey, fromKey)
            if not (fromKey, toKey) in self.weights:
                self.weights[(fromKey, toKey)] = 0
                if commonCategories:
                    common = repository.countCommonCategories(fromKey, toKey)
                    self.commonCategories[(fromKey, toKey)] = common
                    self.weights[(fromKey, toKey)] += self.FACTOR_CATEGORY * math.sqrt(common)
                if commonLinks:
                    common = repository.countCommonLinks(fromKey, toKey)
                    self.commonLinks[(fromKey, toKey)] = common
                    self.weights[(fromKey, toKey)] += self.FACTOR_LINK * math.log(1.0 + common)
            if target == None:
                self.weights[(fromKey, toKey)] += self.WEIGHT_NORMAL
            else:
                self.weights[(fromKey, toKey)] += self.WEIGHT_REDIRECT

    def resetWeights(self):
        self.weights = {}
        self.commonCategories = {}
        self.commonLinks = {}
        for (fromKey, toKey) in self.links:
            target = self.pages[toKey]['redirect']
            if target != None:
                toKey = target
            if fromKey > toKey:
                (fromKey, toKey) = (toKey, fromKey)
            self.weights[(fromKey, toKey)] = 1

class AbstractComponentProcessor:
    LIMIT = 300
    
    def processAll(self):
        self.dataRepository.connect()
        if 'no-big' in self.options.switches:
            incoherent = self.dataRepository.getIncoherent(self.LIMIT)
        else:
            incoherent = self.dataRepository.getIncoherent()
        self.dataRepository.disconnect()
        for compKey in incoherent:
            self.processComponent(compKey, True)

    def processComponent(self, compKey, separate = True):
        if separate:
            self.dataRepository.connect()
        self.log.debug('Processing %s' % compKey)
        pages = self.dataRepository.getComponentPages(compKey)
        links = self.dataRepository.getComponentLanglinks(compKey)
        comp = Component(compKey, pages, links)
        
        if 'common-cats' in self.options.switches:
            comp.updateWeights(self.dataRepository, True, False)

        if 'no-weights' in self.options.switches:
            comp.resetWeights();
        
        self.doProcess(comp)
        if separate:
            self.dataRepository.disconnect()

    def storeMeaning(self, comp):
        revClusters = {}
        for pageKey in comp.pages:
            mainKey = comp.pages[pageKey]['redirect']
            if mainKey == None:
                mainKey = pageKey
            if not comp.clusters[mainKey] in revClusters:
                revClusters[comp.clusters[mainKey]] = [pageKey]
            else:
                revClusters[comp.clusters[mainKey]] += [pageKey]

        self.dataRepository.deletePageMeanings(self.AUTH, comp.key)
        for idx in revClusters:
            meaningPages = revClusters[idx]
            meaningKey = uuid.uuid5(uuid.NAMESPACE_URL, ' '.join(sorted(meaningPages)))
            self.dataRepository.insertPageMeanings(self.AUTH, str(meaningKey), comp.key, meaningPages)
