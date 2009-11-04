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

import logging, math, os, random, sys, uuid, wikitools.analysis.common, xml.dom.minidom

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

        if not pages:
            return

        namespace = None

        clusters = {}
        for pageKey in pages:
            page = pages[pageKey]
            if namespace == None:
                namespace = str(page['namespace'])
            targetKey = page['redirect']
            if targetKey == None:
                targetKey = pageKey
            meaning = meanings[targetKey]
            if not meaning in clusters:
                clusters[meaning] = []
            clusters[meaning] += [pageKey]

        for meaning in clusters:
            clusters[meaning].sort()

        intraLinks = {}
        cuts = []
        for (fromKey, toKey) in links:
            pageFrom = pages[fromKey]
            pageTo = pages[toKey]
            targetKey = pageTo['redirect']
            if targetKey == None:
                targetKey = toKey
            if meanings[fromKey] == meanings[targetKey]:
                meaning = meanings[fromKey]
                if not meaning in intraLinks:
                    intraLinks[meaning] = []
                intraLinks[meaning] += [(fromKey, toKey)]
            else:
                cuts += [(fromKey, toKey)]

        for meaning in intraLinks:
            intraLinks[meaning].sort()
        cuts.sort()

        gotCommon = len(comp.commonCategories) > 0


        impl = xml.dom.minidom.getDOMImplementation()
        doc = impl.createDocument(None, "component", None)
        root = doc.documentElement
        root.setAttribute('id', compKey)
        root.setAttribute('namespace', namespace)

        sortedMeanings = []
        for meaning in clusters:
            sortedMeanings += [meaning]
        sortedMeanings.sort()

        for meaning in sortedMeanings:
            eCluster = doc.createElement('cluster')
            eCluster.setAttribute('id', meaning)
            root.appendChild(eCluster)
            for pageKey in clusters[meaning]:
                ePage = doc.createElement('page')
                eCluster.appendChild(ePage)
                page = pages[pageKey]
                ePage.setAttribute('id', page['key'])
                ePage.setAttribute('lang', page['lang'])
                ePage.setAttribute('title', page['title'].decode('utf-8'))
                if page['redirect'] != None:
                    ePage.setAttribute('redirect', page['redirect'])

            if meaning in intraLinks:
                for (fromKey, toKey) in intraLinks[meaning]:
                    eLink = doc.createElement('link')
                    eCluster.appendChild(eLink)
                    eLink.setAttribute('from', fromKey)
                    eLink.setAttribute('to', toKey)
                    common = 0
                    if gotCommon and not pages[toKey]['redirect']:
                        if fromKey > toKey:
                            (fromKey, toKey) = (toKey, fromKey)
                        common = comp.commonCategories[(fromKey, toKey)]
                    if gotCommon:
                        eLink.setAttribute('common', str(common))

        eIncoherent = doc.createElement('incoherent')
        root.appendChild(eIncoherent)
        
        for (fromKey, toKey) in cuts:
                    eLink = doc.createElement('link')
                    eIncoherent.appendChild(eLink)
                    eLink.setAttribute('from', fromKey)
                    eLink.setAttribute('to', toKey)
                    common = 0
                    if gotCommon and not pages[toKey]['redirect']:
                        if fromKey > toKey:
                            (fromKey, toKey) = (toKey, fromKey)
                        common = comp.commonCategories[(fromKey, toKey)]
                    if gotCommon:
                        eLink.setAttribute('common', str(common))

        xmlDump = root.toprettyxml()
        xmlDump = '<?xml version="1.0" encoding="UTF-8"?>\n' + xmlDump

        path = self.options.outputDir + os.sep + compKey[0:2] + os.sep + compKey[2:4]
        if not os.path.isdir(path):
            os.makedirs(path)
        file = open(path + os.sep + compKey + '.xml', 'w')
        file.write(xmlDump.encode('utf-8'))
        file.close()
