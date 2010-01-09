#!/usr/bin/env python3

"""
This program is designed to clean files from a specified directory.
The program is designed to work together with dbdump.py, so it is
basically designed to clean out regular database dumps. The files
are kept at a certain granularity (so daily backups will be kept
for a month, monthly backups for a year, etc.
Please see the README file for how to use this script and supported
features. You might also try calling this program with '--help'.

Copyright 2009 Mathias Ertl

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

import os, time, sys, calendar, configparser
from optparse import OptionParser


# determine location of (default) config-file. This can still be overridden by
# the command line.
config_file = '/etc/dbclean.conf'
for file in [ './dbclean.conf', '~/.dbclean.conf' ]:
	if os.path.exists( file ) and os.path.isfile( file ) and os.access( file, os.R_OK ):
		config_file = file
		break

# handle command-line:
parser = OptionParser( description="Cleanup regular database dumps and keep copies at a certain granularity for a specified time.", version="%prog 1.0" )
parser.add_option( '--datadir', action='store', type='string', dest='datadir',
	help="Directory where dumps are stored. Each database is assumed to have its own directory. (Default: /var/backups/<section>)" )
parser.add_option( '--format', action='store', type='string', dest='timeformat',
	help="The format the dumps are saved as. See http://docs.python.org/3.0/library/time.html#time.strftime "
		"for a description of the format. (Default: %Y-%m-%d %H:%M:%S)" )
parser.add_option( '--config', action='store', type='string', dest='config',
	help="Location of the config-file (default: /etc/dbclean.conf, ~/.dbclean.conf, ./dbclean.conf)." )
parser.add_option( '--section', action='store', type='string', dest='section',
	default='DEFAULT', help="Section in the config-file to use (default: %default)" )

(options, args) = parser.parse_args()

# this is a safety-measure: %(__name__)s is a bad substitution if the section is 'DEFAULT':
if options.section == 'DEFAULT':
	default_datadir = '/var/backups/DEFAULT'
else:
	default_datadir = '/var/backups/%(__name__)s'

# read config-file:
if options.config != None:
	config_file = options.config
config = configparser.SafeConfigParser({ 'datadir': default_datadir,
	'format': '%%Y-%%m-%%d_%%H:%%M:%%S', 'hourly': '24', 'daily': '31',
	'monthly': '12', 'yearly': '3' } )
config.read( config_file )

# datadir and timeformat may be set via command-line:
if options.datadir:
	datadir = options.datadir
else:
	datadir = config.get( options.section, 'datadir' )
if options.timeformat:
	timeformat = options.timeformat
else:
	timeformat = config.get( options.section, 'format' )

hourly = config.getint( options.section, 'hourly' )
daily = config.getint( options.section, 'daily' )
monthly = config.getint( options.section, 'monthly' )
yearly = config.getint( options.section, 'yearly' )

# some safety-checks
if not os.path.exists( datadir ):
	print( "Error: %s: No such directory." % (datadir) )
elif not os.path.isdir( datadir ):
	print( "Error: %s: Not a directory." % (datadir) )

class backup():
	files = []

	def __init__( self, time, base, file ):
		self.time = time
		self.base = base
		self.files = [ file ]

	def add( self, file ):
		self.files.append( file )

	def is_daily( self ):
		if self.time[3] == 0:
			return True
		else:
			return False

	def is_monthly( self ):
		if self.is_daily() and self.time[2] == 1:
			return True
		else:
			return False
	
	def is_yearly( self ):
		if self.is_monthly() and self.time[1] == 1:
			return True
		else:
			return False

	def remove( self ):
		for file in self.files:
			os.remove( file )

	def __str__( self ):
		return "%s in %s" %(self.files, self.base)

now = time.time()

# loop through each dir in datadir
for dir in os.listdir( datadir ):
	fullpath = os.path.normpath( datadir + '/' + dir )
	if not os.path.isdir( fullpath ):
		print( "Warning: %s: Not a directory." % (fullpath) )
		continue
	os.chdir( fullpath )

	backups = {}

	files = os.listdir( '.' )
	files.sort()

	for file in files:
		filestamp = file.split( '.' )[0]
		timestamp = ''
		try:
			timestamp = time.strptime( filestamp, timeformat )
		except ValueError as e:
			print( '%s: %s' %(file, e) )
		
		if timestamp not in list( backups.keys() ):
			backups[timestamp] = backup( timestamp, fullpath, file )
		else:
			backups[timestamp].add( file )


	for stamp in list(backups.keys()):
		bck = backups[stamp]
		bck_seconds = calendar.timegm( stamp )

		if bck_seconds > now - ( hourly * 3600 ):
#			print ( "%s is hourly and will be kept" % ( time.asctime( stamp ) ) )
			continue
#		else:
#			print ("%s is hourly but to old." % ( time.asctime( stamp ) ) )

		if bck.is_daily():
			if bck_seconds > now - ( daily * 86400 ):
#				print( "%s is daily and will be kept." % ( time.asctime( stamp ) ) )
				continue
#			else:
#				print ("%s is daily but to old." % ( time.asctime( stamp ) ) )

		if bck.is_monthly():
			if bck_seconds > now - ( monthly * 2678400 ):
#				print( "%s is monthly and will be kept." % ( time.asctime( stamp ) ) )
				continue
#			else:
#				print ("%s is monthly but to old." % ( time.asctime( stamp ) ) )
		
		if bck.is_yearly():
			if bck_seconds > now - ( yearly * 31622400 ):
#				print( "%s is yearly and will be kept." % ( time.asctime( stamp ) ) )
				continue
#			else:
#				print ("%s is yearly but to old." % ( time.asctime( stamp ) ) )
#		print( "%s will be removed." % ( time.asctime( stamp ) ) )

		bck.remove()
