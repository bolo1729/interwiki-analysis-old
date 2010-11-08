#!/usr/bin/env python
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

import logging.config, optparse, os, sys

logging.config.fileConfig(os.path.dirname(sys.argv[0]) + os.sep + 'logging.conf')

class Analysis:
	def __init__(self):
		self.log = logging.getLogger('Main')

	def run(self):
		self.parseCommands()
		self.executeCommands()

	def parseCommands(self):
		parser = optparse.OptionParser()
		parser.add_option('-H', '--host', dest='host', default=None, help='set the database host')
		parser.add_option('-P', '--port', dest='port', default=None, help='set the database port')
		parser.add_option('-d', '--database', dest='database', default=None, metavar='DB', help='set the database name')
		parser.add_option('-u', '--user', dest='user', default=None, help='set the database user')
		parser.add_option('-p', '--password', dest='password', default=None, metavar='PASS', help='set the database user\'s password')
		parser.add_option('-i', '--input-dir', dest='inputDir', default='.', metavar='DIR', help='set the input directory')
		parser.add_option('-o', '--output-dir', dest='outputDir', default='.', metavar='DIR', help='set the output directory')
		parser.add_option('-c', '--components', dest='components', default=[], metavar='COMPS', help='set the components to process')
		parser.add_option('-s', '--switches', dest='switches', default=[], help='set additional switches')
		parser.add_option('-r', '--run', dest='commands', default=[], help='run the specified commands')

		(self.opts, _) = parser.parse_args()

		if not self.opts.components:
			self.opts.components = []
		else:
			self.opts.components = self.opts.components.split(',')

		if not self.opts.switches:
			self.opts.switches = []
		else:
			self.opts.switches = self.opts.switches.split(',')

		if not self.opts.commands:
			self.opts.commands = []
		else:
			self.opts.commands = self.opts.commands.split(',')

		if not self.opts.database or not self.opts.user or not self.opts.commands:
			parser.print_help()
			sys.exit(0)

	def executeCommands(self):
		self.log.info('Task(s): ' + ' '.join(self.opts.commands))
		self.doBatch, self.batch = 'batch' in self.opts.switches, []
		for command in self.opts.commands:
			if command == 'import':
				self.execImport()
			if command == 'positions':
				self.execPositions()
			if command == 'cliques':
				self.execCliques()
			if command == 'spatial':
				self.execSpatial()
			if command == 'betweenness':
				self.execBetweenness()
			if command == 'newman-girvan':
				self.execNewmanGirvan()
			if command == 'genetic':
				self.execGenetic()
			if command == 'random':
				self.execRandom()
			if command == 'stats':
				self.execStats()
			if command == 'visualize':
				self.execVisualize()
			if command == 'skel-vis':
				self.execSkelVis()
			if command == 'serialize':
				self.execSerialize()
		if self.doBatch:
			self.execBatch()
		self.log.info('Done.')

	def execBatch(self):
		import wikitools.analysis.batch, wikitools.repo.repository
		dataRepository = wikitools.repo.repository.PostgresqlRepository(host = self.opts.host, port = self.opts.port, database = self.opts.database, user = self.opts.user, password = self.opts.password)
		engine = wikitools.analysis.batch.BatchCalculator(dataRepository, self.opts, self.batch)
		if not self.opts.components:
			engine.processAll()
		else:
			for compKey in self.opts.components:
				engine.processComponent(compKey)
		pass

	def execImport(self):
		import wikitools.importer, wikitools.repo.bigmemory, wikitools.repo.repository
		doBigMemory = 'big-memory' in self.opts.switches
		doMemoryProfile = 'mem-profile' in self.opts.switches
		dataSource = wikitools.importer.DumpsDataSource(self.opts.inputDir)
		if doBigMemory:
			dataRepository = wikitools.repo.bigmemory.BigMemoryPostgresqlRepository(host = self.opts.host, port = self.opts.port, database = self.opts.database, user = self.opts.user, password = self.opts.password)
		else:
			dataRepository = wikitools.repo.repository.PostgresqlRepository(host = self.opts.host, port = self.opts.port, database = self.opts.database, user = self.opts.user, password = self.opts.password, cache = True)
		importer = wikitools.importer.Importer(dataSource, dataRepository, doMemoryProfile)
		importer.doImport()

	def execCommon(self, engineClass):
		if self.doBatch:
			self.batch += [engineClass]
			return
		import wikitools.repo.repository
		dataRepository = wikitools.repo.repository.PostgresqlRepository(host = self.opts.host, port = self.opts.port, database = self.opts.database, user = self.opts.user, password = self.opts.password)
		engine = engineClass(dataRepository, self.opts)
		if not self.opts.components:
			engine.processAll()
		else:
			for compKey in self.opts.components:
				engine.processComponent(compKey)

	def execPositions(self):
		import wikitools.analysis.positions
		self.execCommon(wikitools.analysis.positions.PagePositionCalculator)

	def execCliques(self):
		import wikitools.analysis.cliques
		self.execCommon(wikitools.analysis.cliques.CliquesMeaningCalculator)

	def execSpatial(self):
		import wikitools.analysis.spatial
		self.execCommon(wikitools.analysis.spatial.SpatialMeaningCalculator)

	def execBetweenness(self):
		import wikitools.analysis.betweenness
		self.execCommon(wikitools.analysis.betweenness.BetweennessMeaningCalculator)

	def execNewmanGirvan(self):
		import wikitools.analysis.betweenness
		self.execCommon(wikitools.analysis.betweenness.NewmanGirvanMeaningCalculator)

	def execGenetic(self):
		import wikitools.analysis.genetic
		self.execCommon(wikitools.analysis.genetic.GeneticMeaningCalculator)

	def execRandom(self):
		import wikitools.analysis.rand
		self.execCommon(wikitools.analysis.rand.RandomMeaningCalculator)

	def execStats(self):
		import wikitools.analysis.stats
		self.execCommon(wikitools.analysis.stats.StatsCalculator)

	def execVisualize(self):
		import wikitools.analysis.visual
		self.execCommon(wikitools.analysis.visual.ComponentPainter)

	def execSkelVis(self):
		import wikitools.analysis.skeleton
		self.execCommon(wikitools.analysis.skeleton.SkeletonPainter)

	def execSerialize(self):
		import wikitools.analysis.serializer
		self.execCommon(wikitools.analysis.serializer.ComponentSerializer)

if __name__ == "__main__":
	analysis = Analysis()
	analysis.run()
