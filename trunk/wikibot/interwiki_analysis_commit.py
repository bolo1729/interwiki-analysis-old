#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Commits results of interwiki analyses obtained using this code:
  http://code.google.com/p/interwiki-analysis/

Author:
* Lukasz Bolikowski (Bolo1729)
"""

import optparse, wikipedia, xml.dom.minidom

class InterwikiAnalysisCommit:

    def reportMods(self, add, change, remove):
        msg = []
        if add:
            msg += ['adding: (%s)' % (', '.join(sorted(add)),)]
        if change:
            msg += ['changing: (%s)' % (', '.join(sorted(change)),)]
        if remove:
            msg += ['removing: (%s)' % (', '.join(sorted(remove)),)]
        msg = ', '.join(msg)
        return 'Interwiki analysis ' + msg



    def processMeaning(self, compId, namespace, meaning):
        if self.opts.verbose:
            niceText = '[' + ', '.join(map(lambda p: p[0] + ':' + p[1], meaning)) + ']'
            print 'DEBUG: Processing meaning: %s' % (niceText,)

        # Load pages
        pages = {}
        for page in meaning:
            lang, title = page
            site = wikipedia.getSite(lang)
            page = wikipedia.Page(site, title, site, namespace)
            if self.opts.verbose:
                print 'DEBUG: Fetching page: %s' % (page,)
            if not page.exists():
                print 'WARNING: Skipping this meaning because of nonexistent page: %s' % (page,)
                return
            if page.isRedirectPage():
                print 'WARNING: Skipping this meaning because of unexpected redirect page: %s' % (page,)
                return
            pages[site] = page

        # Update pages
        for page in pages.values():
            interwiki = {}
            for p in page.interwiki():
                interwiki[p.site()] = p

            add, change, remove = [], [], []
            for site in interwiki:
                if not site in pages:
                    remove += [str(site.language())]
                    continue
                if interwiki[site] != pages[site]:
                    change += [str(site.language())]
                    continue
            
            otherPages = {}
            for site in pages:
                if page.site() == site:
                    continue
                otherPages[site] = page
            
            for site in otherPages:
                if not site in interwiki:
                    add += [str(site.language())]
            if not add and not change and not remove:
                continue
            comment = self.reportMods(add, change, remove)
            print 'INFO: page: %s %s' % (page, comment)
            if not self.opts.dry:
                text = wikipedia.replaceLanguageLinks(page.get(), otherPages)
                page.put(text, comment)



    def parseFile(self):
        dom = xml.dom.minidom.parse(self.opts.file)
        xComponent = dom.documentElement

        compId = xComponent.getAttribute('id')
        namespace = int(xComponent.getAttribute('namespace'))

        meanings = []
        for xCluster in xComponent.childNodes:
            if xCluster.nodeType != xml.dom.Node.ELEMENT_NODE:
                continue
            if xCluster.tagName != 'cluster':
                continue
    
            # Now we know we've got a cluster
    
            meaning, langs = [], set()
            for xPage in xCluster.childNodes:
                if xPage.nodeType != xml.dom.Node.ELEMENT_NODE:
                    continue
                if xPage.tagName != 'page':
                    continue
                if xPage.getAttribute('redirect') != '':
                    continue
    
                # Now we know we've got a non-redirect page
    
                lang = xPage.getAttribute('lang')
                title = xPage.getAttribute('title')
                if lang in langs:
                    print 'ERROR: Incoherent XML file, two or more non-redirect pages in language: %s' % (lang,)
                    return
                langs |= set([lang])
                meaning += [(lang, title)]
            meanings += [meaning]
        return (compId, namespace, meanings)



    def main(self):
        optionParser = optparse.OptionParser()
        optionParser.add_option('-f', '--file', dest='file', default=None, help='read analysis results from FILE')
        optionParser.add_option('-n', '--dry-run', action='store_true', dest='dry', default=False, help='do not make any changes')
        optionParser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='be verbose')
    
        (self.opts, _) = optionParser.parse_args()
        if not self.opts.file:
            optionParser.print_help()
            return

        (compId, namespace, meanings) = self.parseFile()
        for meaning in meanings:
            self.processMeaning(compId, namespace, meaning)



if __name__ == "__main__":
    try:
        iac = InterwikiAnalysisCommit()
        iac.main()
    finally:
        wikipedia.stopme()
