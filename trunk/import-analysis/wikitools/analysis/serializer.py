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

class ComponentSerializer(wikitools.analysis.common.AbstractComponentProcessor):
    AUTH = 'analysis.genetic'

    def __init__(self, dataRepository, options):
        self.log = logging.getLogger('ComponentSerializer')
        self.dataRepository = dataRepository
        self.options = options

    def doProcess(self, comp):
        compKey = comp.key
        pages = comp.pages
        links = comp.links
        meanings = self.dataRepository.getComponentPageMeanings(compKey, self.AUTH)
        
        # TODO
