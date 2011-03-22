#!/usr/bin/python3

"""
This program is designed to regulary dump SQL databases into a 
specified directory for backup purposes. Please see the README file
for how to use this script and supported features. You might also
try calling this program with '--help'.

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

import time, os, sys
from libdump import *
from optparse import OptionParser, OptionGroup

parser = OptionParser( description="Dump databases to a specified directory.", version="%prog 1.0" )
parser.add_option( '--backend', action='store',
	type='string', dest='backend', default='mysql',
	help="Specify the backend to use. This script currently supports postgresql and mysql." )
parser.add_option( '--datadir', action='store', 
	type='string', dest='datadir', default='/var/backups/',
	help="Safe the dumps to DATADIR. If used with --remote, DATADIR is a "
	"directory on the remote machine. (Default: %default)" )
parser.add_option( '--su', action='store', dest='su',
	help="Execute all sql-commands as user SU." )
parser.add_option( '--remote', action='store', dest='remote',
	help='Store dumps remote via SSH. REMOTE will be passed to ssh unchanged.'
	' Example: "user@backup.example.com"' )
parser.add_option( '--sign', action='store', dest='sign_key',
	help='Use gpg to sign the dump using the key SIGN_KEY' )
parser.add_option( '--encrypt', action='store', dest='recipient',
	help='Use gpg to encrypt the dumps for RECIPIENT.' )

group = OptionGroup(parser, "MySQL options",
	"These options are only available when using --backend=mysql." )
group.add_option( '--defaults', action='store', 
	type='string', dest='defaults', default='~/.my.cnf',
	help="Defaults-file to connect to your mysql-server (Default: %default)" )
group.add_option( '--ignore-table', action='append', dest="ignore_tables",
	metavar='DB_NAME.DB_TABLE',
	help="""Do not dump the given table. Use multiple times to skip more than
one table.""" )
parser.add_option_group( group )

group = OptionGroup( parser, "PostgreSQL options",
	"These options are only available when using --backend=postgresql" )
group.add_option( '--psql-options', action='store', dest='psql_opts',
	help="PSQL-OPTS will be passed unmodified to psql" )
group.add_option( '--pg_dump-options', action='store', dest='pgdump_opts',
	help="PGDUMP_OPTS will be passed unmodified to pg_dump" )
parser.add_option_group( group )

group = OptionGroup( parser, "ejabberd options",
	"These options are only available when using --backend=ejabberd" )
group.add_option( '--node', action="store",
	help="Dump database from this ejabberd node (optional)" )
group.add_option( '--auth', action="store", nargs=3,
	metavar="USER HOST PASSWORD",
	help="Authenticate with the erlang node. This specifies a normal "
		"account on the jabber server." )
group.add_option( '--base-dir', action="store", default="/var/lib/ejabberd",
	help="Base directory where the ejabberd database is stored" )
parser.add_option_group( group )

(options, args) = parser.parse_args()

if not options.remote:
	# Note that if we are remote there is no real way to check to check if
	# base exists and is writeable. We rely on the competence of the admin
	# in that case.
	base = options.datadir
	if not os.path.exists( base ):
		print( "Error: " + base + ": Does not exist." )
		sys.exit( 1 )
	elif not os.path.isdir( base ):
		print( "Error: " + base + ": Not a directory." )
		sys.exit( 1 )
	elif not os.access( base, (os.R_OK | os.W_OK | os.X_OK) ):
		print( "Error: " + base + ": Permission denied." )
		sys.exit( 1 )

if options.backend == "mysql":
	backend = mysql.mysql( options )
elif options.backend == "postgresql":
	backend = postgresql.postgresql( options )
elif options.backend == "ejabberd":
	backend = ejabberd.ejabberd( options )
else:
	parser.error( "Unknown backend specified. This script only supports mysql and postgresql." )

databases = backend.get_db_list()
timestamp = time.strftime( '%Y-%m-%d_%H:%M:%S', time.gmtime() )

# finally: loop through the databases and dump them:
backend.prepare()
for database in databases:
	try:
		backend.prepare_db( database )
		backend.dump( database, timestamp )
		backend.cleanup_db( database )
	except Exception as e:
		print( e )
		continue
	if database != databases[-1]:
		time.sleep(3)

backend.cleanup()
