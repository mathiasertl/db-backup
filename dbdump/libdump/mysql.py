"""
This file is part of dbdump.

Copyright 2009, 2010 Mathias Ertl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from libdump import backend
from subprocess import *
import os, sys, stat

class mysql( backend.backend ):
	def prepare( self ):
		defaults = os.path.expanduser( self.options.defaults )
		if not os.path.exists( defaults ):
			print( "Error: %s: Does not exist."%defaults )
			sys.exit(1)
		unsafe = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
		unsafe |= stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH

		mode = os.stat( defaults )[stat.ST_MODE]
		if mode & unsafe != 0:
			print( "Warning: %s: unsafe permissions (fix with 'chmod go-rwx %s'"%(defaults, defaults) )

	def get_db_list( self ):
		cmd = [ '/usr/bin/mysql', '--defaults-file=' + self.options.defaults, '--execute=SHOW DATABASES', '-B', '-s' ]
		p_list = Popen( cmd, stdout=PIPE, stderr=PIPE )
		stdout, stderr = p_list.communicate()
		databases = stdout.decode().strip("\n").split("\n")
		p_list.wait()

		if p_list.returncode != 0:
			raise Exception( "Unable to get list of databases: %s "
				% ( stderr.decode().strip("\n") ) )

		return [ db for db in databases if db != 'information_schema' ]

	def get_command( self, database ):
		# get list of ignored tables:
		ignored = [ t for t in self.options.ignore_tables if t.startswith( "%s."%database ) ]

		# assemble query for used engines in the database
		engine_query = "select ENGINE from information_schema.TABLES WHERE TABLE_SCHEMA='%s' AND ENGINE != 'MEMORY'"%database
		for table in ignored:
			engine_query += " AND TABLE_NAME != '%s'"%table.split('.')[1]
		engine_query += ' GROUP BY ENGINE'

		engine_cmd = [ 'mysql' ]
		if self.options.defaults:
			engine_cmd.append( '--defaults-file=%s' %(self.options.defaults) )
		engine_cmd += [ '-NB', "--execute=%s"%engine_query ]
		p = Popen( engine_cmd, stdout=PIPE )
		types = p.communicate()[0].decode('utf-8').strip().split("\n")

		cmd = [ 'mysqldump' ]
		if self.options.defaults:
			cmd.append( '--defaults-file=%s' %(self.options.defaults) )

		for table in ignored:
			cmd.append( '--ignore-table="%s"'%table )

		if types == [ 'InnoDB' ]:
			cmd.append( '--single-transaction' )
			cmd.append( '--quick' )
		else:
			cmd.append( '--lock-tables' )

		cmd += [ '--comments', database ]
		return cmd
