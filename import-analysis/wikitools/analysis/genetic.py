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

import logging, math, os, random, sys, wikitools.analysis.common, uuid

class GeneticMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'genetic'
    AUTH = 'analysis.genetic'
    REDIRECT = 0.01
    GEN_SIZE = 100
    RND_SIZE = 10
    MUTATION = 0.05
    STAGNATION = 5

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('GeneticMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

    def doProcess(self, comp):
        ordered = []
        for (f, t) in comp.mLinks:
            ordered += [(f, t)]

        # First generation
        generation = []
        for _ in xrange(self.GEN_SIZE):
            generation += [self.randomCut(comp.pages, comp.mPages, comp.weights, ordered)]

        bestFitnessEver, bestEverAge = -1.0, -1
        while True:
            bestEverAge += 1
            if bestEverAge > self.STAGNATION:
                break
            
            # Setting up the roulette
            rCandidate = []
            rCumFitness = []
            sumFitness, bestCandidateNow, bestFitnessNow = 0.0, None, -1.0
            for candidate in generation:
                fitness = self.fitness(comp.pages, comp.mPages, comp.weights, ordered, candidate)
                if (fitness > bestFitnessNow):
                    bestCandidateNow = candidate
                    bestFitnessNow = fitness
                sumFitness += fitness
                rCandidate += [candidate]
                rCumFitness += [sumFitness]
            
            self.log.debug('Avg. fitness of this generation: %8.8f, best: %8.8f' % (sumFitness / len(generation), bestFitnessNow))
            
            if bestFitnessEver < bestFitnessNow:
                bestFitnessEver = bestFitnessNow
                bestCandidateEver = bestCandidateNow
                bestEverAge = 0
            
            # Choosing parents
            parents = []
            for _ in xrange(len(generation) - self.RND_SIZE):
                r = random.uniform(0, sumFitness)
                c = None
                for i in xrange(len(rCumFitness)):
                    if r <= rCumFitness[i]:
                        c = rCandidate[i]
                        break
                parents += [c]
            for _ in xrange(self.RND_SIZE):
                parents += [self.randomCut(comp.pages, comp.mPages, comp.weights, ordered)]

            # Generating offspring
            nextGeneration = []
            for i in xrange(len(parents) / 2):
                (o1, o2) = self.offspring(comp.pages, comp.mPages, comp.weights, ordered, parents[2*i], parents[2*i + 1])
                nextGeneration += [o1, o2]

            generation = nextGeneration

        cut = set()
        for i in bestCandidateEver:
            cut |= set([ordered[i]])
        
        comp.setCut(cut)

        self.storeMeaning(comp)
        
        cost = self.distance(comp.pages, comp.mPages, comp.weights, ordered, bestCandidateEver)
        self.log.info('Total cost: %s %d' % (comp.key, cost))

    def offspring(self, pages, vertices, edges, ordered, c1, c2):
        cs = set(c1) | set(c2)
        n = len(edges)
        p1, p2 = [], []
        for i in xrange(n):
            if not i in cs:
                p1 += [i]
                p2 += [i]
        
        t = []
        for c in cs:
            t += [c]

        random.shuffle(t)
        for i in t:
            p1 += [i]
        random.shuffle(t)
        for i in t:
            p2 += [i]
        if (n > 2):
            if (random.random() < self.MUTATION):
                m1 = random.randint(0, n - 1)
                m2 = random.randint(0, n - 1)
                p1[m1], p1[m2] = p1[m2], p1[m1]
            if (random.random() < self.MUTATION):
                m1 = random.randint(0, n - 1)
                m2 = random.randint(0, n - 1)
                p2[m1], p2[m2] = p2[m2], p2[m1]

        o1 = self.findCut(pages, vertices, edges, ordered, p1)
        o2 = self.findCut(pages, vertices, edges, ordered, p2)

        return (o1, o2)

    def fitness(self, pages, vertices, edges, ordered, cut):
        dist = self.distance(pages, vertices, edges, ordered, cut)
        return 1.0 / (1.0 + math.sqrt(dist))

    def distance(self, pages, vertices, edges, ordered, cut):
        dist = 0
        for c in cut:
            dist += edges[ordered[c]]
        return dist

    def findCut(self, pages, vertices, edges, ordered, permutation):
        ret = self.findCutAndClusters(pages, vertices, edges, ordered, permutation)
        return ret[0]

    def findClusters(self, pages, vertices, edges, ordered, permutation):
        ret = self.findCutAndClusters(pages, vertices, edges, ordered, permutation)
        return ret[1]
        
    def findCutAndClusters(self, pages, vertices, edges, ordered, permutation):
        clusters, langs, idx = {}, {}, 0
        for pageKey in vertices:
            page = pages[pageKey]
            lang = page['lang']
            
            clusters[pageKey] = idx
            langs[idx] = set([lang])
            idx += 1

        cut = set()
        for p in permutation:
            (f, t) = ordered[p]
            (cf, ct) = clusters[f], clusters[t]
            if cf == ct:
                continue
            if langs[cf] & langs[ct] != set():
                cut |= set([p])
                continue
            # Merge
            langs[cf] = langs[cf] | langs[ct]
            for v in vertices:
                if (clusters[v] == ct):
                    clusters[v] = cf
        return (cut, clusters)

    def randomCut(self, pages, vertices, edges, ordered):
        permutation = range(len(ordered))
        random.shuffle(permutation)
        return self.findCut(pages, vertices, edges, ordered, permutation)
