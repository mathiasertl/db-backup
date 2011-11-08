from libdump import backend
import subprocess, os

class ejabberd( backend.backend ):
	def get_db_list( self ):
		return [ 'ejabberd' ]

	def get_command( self, database ):
		path = os.path.normpath( self.options.base_dir + '/' + database + '.backup' )
		return [ 'cat', path ]
		
	def prepare_db( self, database ):
		cmd = [ 'ejabberdctl' ]
		if self.options.node:
			cmd += [ '--node', self.options.node ]
		if self.options.auth:
			cmd.append( '--auth' )
			cmd += list( self.options.auth )

		cmd += [ 'backup', database + '.backup' ]
		p = subprocess.Popen( cmd )
		p.communicate()

	def cleanup_db( self, database ):
		path = os.path.normpath( self.options.base_dir + '/' + database + '.backup' )
		os.remove( path )
