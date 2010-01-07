from libdump import backend
from subprocess import *

class postgresql( backend.backend ):
	def get_db_list( self ):
		cmd = [ 'psql', '-lAq' ]

		if self.options.psql_opts:
			cmd += self.options.psql_opts.split( ' ' )

		if self.options.su:
			cmd = [ 'su', 'postgres', '-s', '/bin/bash', '-c', ' '.join( cmd ) ]

		p_list = Popen( cmd, stdout=PIPE, stderr=PIPE )
		stdout, stderr = p_list.communicate()
		databases = []
		for line in stdout.decode().split( "\n" )[2:][:-2]:
			db = line.split( '|' )[0]
			if db == "template0":
				continue
			databases.append( db )

		p_list.wait()
		if p_list.returncode != 0:
			raise Exception( "Unable to get list of databases: %s "
				% ( stderr.decode().strip("\n") ) )


		return databases

	def get_command( self, database ):
		cmd = [ 'pg_dump' ]
		if self.options.pgdump_opts:
			cmd += self.options.pgdump_opts.split( ' ' )
		cmd.append( database )
		return cmd

