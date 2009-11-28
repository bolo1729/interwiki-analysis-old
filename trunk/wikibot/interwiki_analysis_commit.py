#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Commits results of an externally conducted interwiki analysis.

The script reads an XML file describing directions for a given
set of pages, and adds/changes/removes interwiki links
in accordance with the directions.

An input XML file should contain a partition of a set of pages
into clusters.  Example:

  <?xml version="1.0" encoding="UTF-8"?>
  <component id="0dd602cb-fde0-5eff-aa33-4eb1635b6fe9" namespace="14">
    <cluster>
      <page lang="en" title="Transportation in Costa Rica"/>
      <page lang="id" title="Transportasi di Kosta Rika"/>
      <page lang="it" title="Trasporti in Costa Rica"/>
    </cluster>
    <cluster>
      <page lang="id" title="Transportasi di Amerika Tengah"/>
    </cluster>
  </component>

The script makes sure that any given page contains interwiki
links to all the other pages in the same cluster, and contains
no other interwiki links.

The script can run in "dry run" mode, in which no changes to
any page are actually made.  For a list of options, run the
script with '--help' option.

Here's a tool generating interwiki analyses in the format
accepted by this script:
  http://code.google.com/p/interwiki-analysis/
"""

import optparse, wikipedia, xml.dom.minidom

__author__ = 'Lukasz Bolikowski'
__license__ = 'GNU GPL version 3'
__version__ = '1.0'

class InterwikiAnalysisCommit:
    """Commits results of an externally conducted interwiki analysis."""

    def reportMods(self, add, change, remove):
        """Generates an edit summary."""
        msg = []
        if add:
            msg += ['adding: (%s)' % (', '.join(sorted(add)),)]
        if change:
            msg += ['changing: (%s)' % (', '.join(sorted(change)),)]
        if remove:
            msg += ['removing: (%s)' % (', '.join(sorted(remove)),)]
        msg = ', '.join(msg)
        return 'Interwiki analysis ' + msg



    def processMeaning(self, compId, namespace, activeLangs, meaning):
        """Updates all the pages in a given cluster."""
        if self.opts.verbose:
            niceText = '[' + ', '.join(map(lambda p: p[0] + ':' + p[1], meaning)) + ']'
            print 'DEBUG: Processing meaning: %s' % (niceText,)

        # Load pages
        pages = {}
        for page in meaning:
            lang, title = page
            if not lang in activeLangs:
                continue
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

        # Process each page
        for page in pages.values():
            interwiki = {}
            for p in page.interwiki():
                interwiki[p.site()] = p

            # Find interwikis to add/change/remove
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

            # Check if update needed
            if not add and not change and not remove:
                continue
            
            # Update the page
            comment = self.reportMods(add, change, remove)
            print 'INFO: page: %s %s' % (page, comment)
            if not self.opts.dry:
                text = wikipedia.replaceLanguageLinks(page.get(), otherPages)
                page.put(text, comment)



    def dropInactive(self, langs):
        """Filters out the inactive language editions."""
        activeLangs = set()
        for lang in langs:
            try:
                if wikipedia.getSite(lang):
                    activeLangs |= set([lang])
            except wikipedia.NoSuchSite:
                if self.opts.verbose:
                    print 'DEBUG: Ignoring inactive lang: %s' % (lang,)
                pass
        return activeLangs



    def parseFile(self):
        """Parses the XML file specified in cmdline options."""
        dom = xml.dom.minidom.parse(self.opts.file)
        xComponent = dom.documentElement

        compId = xComponent.getAttribute('id')
        namespace = int(xComponent.getAttribute('namespace'))

        meanings, encounteredLangs = [], set()
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
                encounteredLangs |= set([lang])
                title = xPage.getAttribute('title')
                if lang in langs:
                    print 'ERROR: Incoherent XML file, two or more non-redirect pages in language: %s' % (lang,)
                    return (compId, namespace, [], [])
                langs |= set([lang])
                meaning += [(lang, title)]
            meanings += [meaning]
        return (compId, namespace, encounteredLangs, meanings)



    def main(self):
        """Main routine."""

        # Parse command line options
        optionParser = optparse.OptionParser()
        optionParser.add_option('-f', '--file', dest='file', default=None, help='read analysis results from FILE')
        optionParser.add_option('-n', '--dry-run', action='store_true', dest='dry', default=False, help='do not make any changes')
        optionParser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False, help='be verbose')
        (self.opts, _) = optionParser.parse_args()
        if not self.opts.file:
            optionParser.print_help()
            return

        # Parse the XML file
        (compId, namespace, langs, meanings) = self.parseFile()
        langs = self.dropInactive(langs)
        for meaning in meanings:
            # Update pages in the given cluster
            self.processMeaning(compId, namespace, langs, meaning)



if __name__ == "__main__":
    try:
        iac = InterwikiAnalysisCommit()
        iac.main()
    finally:
        wikipedia.stopme()
