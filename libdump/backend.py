import os, time
from subprocess import *

class backend():
	def __init__( self, options ):
		self.options = options
		self.base = options.datadir
		if self.options.sign_key or self.options.recipient:
			self.gpg = True
		else:
			self.gpg = False

	def make_su( self, cmd ):
		if self.options.su:
			cmd = [ 'su', self.options.su, '-s', '/bin/bash', '-c', ' '.join( cmd ) ]
		return cmd

	def get_ssh( self, path, cmds ):
		cmds = [ ' '.join( cmd ) for cmd in cmds ]
		prefix = 'umask 077; mkdir -m 0700 -p %s; ' %(os.path.dirname(path))
		ssh_cmd = prefix + ' | '.join( cmds ) + ' > %s.md5' %(path)
		return [ 'ssh', self.options.remote, ssh_cmd ]

	def dump( self, db, timestamp ):
		cmd = self.make_su( self.get_command( db ) )

		dir = os.path.normpath( self.base + '/' + db )
		path = os.path.normpath( dir + '/' + timestamp )
		if self.gpg:
#			gpg = [ 'gpg', '-ser', self.options.gpg, '-' ]
			gpg = [ 'gpg' ]
			if self.options.sign_key:
				gpg += [ '-s', '-u', self.options.sign_key ]
			if self.options.recipient:
				gpg += [ '-e', '-r', self.options.recipient ]
			path += '.gpg'
				
		path += '.gz'

		gzip = [ 'gzip', '-f', '-9', '-', '-' ]
		tee = [ 'tee', path ]
		md5sum = [ 'md5sum' ]
		sed = [ 'sed', 's/-$/%s/' %(os.path.basename( path ) ) ]

		if self.options.remote:
			ssh = self.get_ssh( path, [gzip, tee, md5sum, sed] )

			p1 = Popen( cmd, stdout=PIPE )
			p = p1
			if self.gpg:
				p = Popen( gpg, stdin=p1.stdout, stdout=PIPE )

			p2 = Popen( ssh, stdin=p.stdout, stdout=PIPE )
			output = p2.communicate()[0]
		else:   
			if not os.path.exists( dir ):
				os.mkdir( dir, 0o700 )

			f = open( path + '.md5', 'w' )
			p1 = Popen( cmd, stdout=PIPE )
			p = p1
			if self.gpg:
				p = Popen( gpg, stdin=p1.stdout, stdout=PIPE )
			p2 = Popen( gzip, stdin=p1.stdout, stdout=PIPE )
			p3 = Popen( tee, stdin=p2.stdout, stdout=PIPE )
			p4 = Popen( md5sum, stdin=p3.stdout, stdout=PIPE )
			p5 = Popen( sed, stdin=p4.stdout, stdout=f )
			p5.communicate()
			f.close()
		time.sleep( 5 )

