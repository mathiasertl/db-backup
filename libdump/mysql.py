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
