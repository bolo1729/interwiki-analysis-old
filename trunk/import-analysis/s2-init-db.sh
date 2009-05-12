#!/bin/bash
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


# Initializes the database where preprocessed links will be stored.
# Change 'wikidb' to a name of your choice.  Also, you might need
# to create a user, grant permissions, etc.  Refer to the PostgreSQL
# docs for details.

createdb wikidb
psql wikidb -f schema.sql
