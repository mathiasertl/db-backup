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

class mysql( backend.backend ):
	def get_db_list( self ):
		cmd = [ '/usr/bin/mysql', '--defaults-file=' + self.options.defaults, '--execute=SHOW DATABASES', '-B', '-s' ]
		p_list = Popen( cmd, stdout=PIPE, stderr=PIPE )
		stdout, stderr = p_list.communicate()
		databases = stdout.decode().strip("\n").split("\n")
		p_list.wait()

		if p_list.returncode != 0:
			raise Exception( "Unable to get list of databases: %s "
				% ( stderr.decode().strip("\n") ) )

		return databases

	def get_command( self, database ):
		cmd = [ 'mysqldump' ]
		if self.options.defaults:
			cmd.append( '--defaults-file=%s' %(self.options.defaults) )
		cmd += [ '--comments', database ]
		return cmd
