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
    pass

class CliquesMeaningCalculator(wikitools.analysis.common.AbstractComponentProcessor):
    NAME = 'cliques'
    AUTH = 'analysis.cliques'
    
    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('CliquesMeaningCalculator')
        self.dataRepository = dataRepository
        self.options = options

    def doProcess(self, comp):
        lookup = {}
        for pageKey in comp.mPages:
            c = comp.clusters[pageKey]
            if c in lookup:
                raise Exception, 'Someone touched my clusters!'
            lookup[c] = set([pageKey])
        
        # TODO
        
        cost = -1
        self.log.info('Total cost: %s %d' % (comp.key, cost))
        
        # self.storeMeaning(comp)
