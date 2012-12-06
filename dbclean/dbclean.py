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

import os, time, sys, calendar, configparser, argparse

config_file = ['/etc/dbclean/dbclean.conf', os.path.expanduser('~/.dbclean.conf')]

parser = argparse.ArgumentParser(version="%prog 1.0",
    description = """Cleanup regular database dumps created by dbdump. This script keeps backups
        at given intervals for a given amount of time.""")
parser.add_argument('-c', '--config', type=str, dest='config', action='append', default=config_file,
    help="""Additional config-files to use (default: %(default)s). Can be given multiple times
        to name multiple config-files.""")
parser.add_argument('section', action='store', type=str,
    help="Section in the config-file to use." )
args = parser.parse_args()

if args.section=='DEFAULT':
    parser.error("--section must not be 'DEFAULT'.")

config = configparser.SafeConfigParser({
    'format': '%%Y-%%m-%%d_%%H:%%M:%%S',
    'hourly': '24', 'daily': '31',
    'monthly': '12', 'yearly': '3'
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

# get directory containing backups:
datadir = config.get(args.section, 'datadir')

# check that given directory exists and is a directory:
if not os.path.exists(datadir):
    print("Error: %s: No such directory." % (datadir), file=sys.stderr)
    sys.exit(1)
elif not os.path.isdir(datadir):
    print("Error: %s: Not a directory." % (datadir), file=sys.stderr)
    sys.exit(1)

timeformat = config[args.section]['format']
hourly = int(config[args.section]['hourly'])
daily = int(config[args.section]['daily'])
monthly = int(config[args.section]['monthly'])
yearly = int(config[args.section]['yearly'])

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
    if dir.startswith( '.' ):
        # skip hidden directories
        continue

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
#            print ( "%s is hourly and will be kept" % ( time.asctime( stamp ) ) )
            continue
#        else:
#            print ("%s is hourly but to old." % ( time.asctime( stamp ) ) )

        if bck.is_daily():
            if bck_seconds > now - ( daily * 86400 ):
#                print( "%s is daily and will be kept." % ( time.asctime( stamp ) ) )
                continue
#            else:
#                print ("%s is daily but to old." % ( time.asctime( stamp ) ) )

        if bck.is_monthly():
            if bck_seconds > now - ( monthly * 2678400 ):
#                print( "%s is monthly and will be kept." % ( time.asctime( stamp ) ) )
                continue
#            else:
#                print ("%s is monthly but to old." % ( time.asctime( stamp ) ) )

        if bck.is_yearly():
            if bck_seconds > now - ( yearly * 31622400 ):
#                print( "%s is yearly and will be kept." % ( time.asctime( stamp ) ) )
                continue
#            else:
#                print ("%s is yearly but to old." % ( time.asctime( stamp ) ) )
#        print( "%s will be removed." % ( time.asctime( stamp ) ) )

        bck.remove()
