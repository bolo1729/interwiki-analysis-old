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

import getopt, logging.config, os, sys, wikitools.repo.bigmemory, wikitools.importer, wikitools.repo.repository

logging.config.fileConfig(os.path.dirname(sys.argv[0]) + os.sep + 'logging.conf')

def usage():
	print 'Usage:'
	print '  %s [-H <host>] [-P <port>] -d <database> -u <user> [-p <password>] [-i <importDir>] [-b] [-m]' % sys.argv[0]
	print '  %s [--host=<host>] [--port=<port>] --database=<database> --user=<user> [--password=<password>] [--import-dir=<importDir>] [--big-memory] [--mem-profile]' % sys.argv[0]
	print '  %s -h' % sys.argv[0]
	print '  %s --help' % sys.argv[0]
	sys.exit(0)

optlist, args = getopt.getopt(sys.argv[1:], 'H:P:d:u:p:i:bmh', ['host=', 'port=', 'database=', 'user=', 'password=', 'import-dir=', 'big-memory', 'mem-profile', 'help'])
(host, port, database, user, password, importDir, bigMemory, memProfile) = (None, None, None, None, None, '.', False, False)
for opt, arg in optlist:
	if opt in ('-H', '--host'): host = arg
	if opt in ('-P', '--port'): port = arg
	if opt in ('-d', '--database'): database = arg
	if opt in ('-u', '--user'): user = arg
	if opt in ('-p', '--password'): password = arg
	if opt in ('-i', '--import-dir'): importDir = arg
	if opt in ('-b', '--big-memory'): bigMemory = True
	if opt in ('-m', '--mem-profile'): memProfile = True
	if opt in ('-h', '--help'): usage()
if not database or not user: usage()

dataSource = wikitools.importer.DumpsDataSource(importDir)
if bigMemory:
	dataRepository = wikitools.repo.bigmemory.BigMemoryPostgresqlRepository(host = host, port = port, database = database, user = user, password = password)
else:
	dataRepository = wikitools.repo.repository.PostgresqlRepository(host = host, port = port, database = database, user = user, password = password)
importer = wikitools.importer.Importer(dataSource, dataRepository, memProfile)

importer.doImport()
