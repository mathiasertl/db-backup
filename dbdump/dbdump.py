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

import os, sys, time, argparse
from libdump import *

config_file = ['/etc/dbdump/dbdump.conf', os.path.expanduser('~/.dbdump.conf')]

parser = argparse.ArgumentParser(version="%prog 1.0",
    description="Dump databases to a specified directory.")
parser.add_argument('-c', '--config', type=str, dest='config', action='append', default=config_file,
    help="""Additional config-files to use (default: %(default)s). Can be given multiple times
        to name multiple config-files.""")
parser.add_argument('section', action='store', type=str,
    help="Section in the config-file to use." )
args = parser.parse_args()

# old options:
"""
parser.add_argument('--backend', action='store', default='mysql',
    help="Specify the backend to use. This script currently supports postgresql and mysql.")
parser.add_argument('--datadir', action='store', default='/var/backups/',
    help="Safe the dumps to DATADIR. If used with --remote, DATADIR is a "
        "directory on the remote machine. (Default: %(default)s)")
parser.add_argument('--su', action='store',
    help="Execute all sql-commands as user SU.")
parser.add_argument('--remote', action='store',
    help='Store dumps remote via SSH. REMOTE will be passed to ssh unchanged.'
    ' Example: "user@backup.example.com"')
parser.add_argument('--sign', action='store', dest='sign_key',
    help='Use gpg to sign the dump using the key SIGN_KEY')
parser.add_argument('--encrypt', action='store', dest='recipient',
    help='Use gpg to encrypt the dumps for RECIPIENT.')

group = parser.add_argument_group(title="MySQL options",
    description="These options are only available when using --backend=mysql.")
group.add_argument('--defaults', action='store', default='~/.my.cnf',
    help="Defaults-file to connect to your mysql-server (Default: %(default)s)")
group.add_argument('--ignore-table', action='append', dest="ignore_tables",
    metavar='DB_NAME.DB_TABLE', default=[],
    help='Do not dump the given table. Use multiple times to skip more than one table.')

group = parser.add_argument_group(title="PostgreSQL options",
    description="These options are only available when using --backend=postgresql")
group.add_argument('--psql-options', action='store', dest='psql_opts',
    help="PSQL-OPTS will be passed unmodified to psql")
group.add_argument('--pg_dump-options', action='store', dest='pgdump_opts',
    help="PGDUMP_OPTS will be passed unmodified to pg_dump")

group = parser.add_argument_group(title="ejabberd options",
    description="These options are only available when using --backend=ejabberd")
group.add_argument('--node', action="store",
    help="Dump database from this ejabberd node (optional)")
group.add_argument('--auth', action="store", nargs=3, metavar=('USER', 'HOST', 'PASSWORD',),
    help="Authenticate with the erlang node. This specifies a normal account on the jabber server.")
group.add_argument('--base-dir', action="store", default="/var/lib/ejabberd",
    help="Base directory where the ejabberd database is stored")
"""

args = parser.parse_args()

if args.section=='DEFAULT':
    parser.error("--section must not be 'DEFAULT'.")
    
config = configparser.SafeConfigParser({
    'format': '%%Y-%%m-%%d_%%H:%%M:%%S',
})
if not config.read(args.config):
    parser.error("No config-files could be read.")
    
# check validity of config-file:
if args.section not in config:
    print("Error: %s: No section found with that name." % args.section, file=sys.stderr)
    sys.exit(1)
if 'datadir' not in config[args.section]:
    print("Error: %s: Section does not contain option 'datadir'." % args.section, file=sys.stderr)
    sys.exit(1)
    
section = config[args.section]

if 'remote' not in section:
    # Note that if we dump to a remote location, there is no real way to check to check if datadir
    # exists and is writeable. We have to rely on the competence of the admin in that case.
    datadir = section['datadir']
    if not os.path.exists(datadir):
        print("Error: %s: Does not exist." % datadir, sys.stderr)
        sys.exit(1)
    elif not os.path.isdir(datadir):
        print("Error: %s: Not a directory." % datadir, sys.stderr)
        sys.exit(1)
    elif not os.access( base, (os.R_OK | os.W_OK | os.X_OK)):
        print("Error: %s: Permission denied." % datadir, sys.stderr)
        sys.exit(1)

if section['backend'] == "mysql":
    backend = mysql.mysql(args)
elif section['backend'] == "postgresql":
    backend = postgresql.postgresql(args)
elif section['backend'] == "ejabberd":
    backend = ejabberd.ejabberd(args)
else:
    print("Error: %s. Unknown backend specified. Only mysql, postgresql and ejabberd are supported."
        % section['backend'], file=sys.stderr)
    sys.exit(1)

databases = backend.get_db_list()
timestamp = time.strftime(section['format'], time.gmtime())

# finally: loop through the databases and dump them:
backend.prepare()
for database in databases:
    try:
        backend.prepare_db(database)
        backend.dump(database, timestamp)
        backend.cleanup_db(database)
    except RuntimeError as e:
        print(e)
        break
    except Exception as e:
        print(e)
        continue
    if database != databases[-1]:
        time.sleep(3)

backend.cleanup()