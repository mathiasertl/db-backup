#!/usr/bin/env python3
#
# This program is designed to clean files from a specified directory.  The program is designed to
# work together with dbdump.py, so it is basically designed to clean out regular database dumps.
# The files are kept at a certain granularity (so daily backups will be kept for a month, monthly
# backups for a year, etc.  Please see the README file for how to use this script and supported
# features. You might also try calling this program with '--help'.
#
# Copyright 2009 - 2019 Mathias Ertl <mati@fsinf.at>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import calendar
import configparser
import os
import sys
import time


def err(msg, *args):
    print(msg % args, file=sys.stderr)


config_file = [
    '/etc/dbclean/dbclean.conf',
    os.path.expanduser('~/.dbclean.conf')
]

parser = argparse.ArgumentParser(
    description="""Cleanup regular database dumps created by dbdump. This script keeps backups at
given intervals for a given amount of time.""")
parser.add_argument('--version', action='version', version='%(prog)s 1.1')
parser.add_argument(
    '-c', '--config', type=str, dest='config', action='append',
    default=config_file, help="""Additional config-files to use (default: %(default)s). Can be
        given multiple times to name multiple config-files.""")
parser.add_argument('section', action='store', type=str, help="Section in the config-file to use.")
args = parser.parse_args()

if args.section == 'DEFAULT':
    parser.error("--section must not be 'DEFAULT'.")

config = configparser.SafeConfigParser({
    'format': '%%Y-%%m-%%d_%%H:%%M:%%S',
    'hourly': '24', 'daily': '31',
    'monthly': '12', 'yearly': '3',
    'last': '3',
})
if not config.read(args.config):
    parser.error("No config-files could be read.")

# check validity of config-file:
if args.section not in config:
    err("Error: %s: No section found with that name.", args.section)
    sys.exit(1)
if 'datadir' not in config[args.section]:
    err("Error: %s: Section does not contain option 'datadir'.", args.section)
    sys.exit(1)

# get directory containing backups:
datadir = config.get(args.section, 'datadir')

# check that given directory exists and is a directory:
if not os.path.exists(datadir):
    err("Error: %s: No such directory.", datadir)
    sys.exit(1)
elif not os.path.isdir(datadir):
    err("Error: %s: Not a directory.", datadir)
    sys.exit(1)

timeformat = config[args.section]['format']
hourly = int(config[args.section]['hourly'])
daily = int(config[args.section]['daily'])
monthly = int(config[args.section]['monthly'])
yearly = int(config[args.section]['yearly'])
last = int(config[args.section]['last'])
now = time.time()


class backup():
    files = []

    def __init__(self, time, base, file):
        self.time = time
        self.base = base
        self.files = [file]

    def add(self, file):
        self.files.append(file)

    def is_daily(self):
        if self.time.tm_hour == 0:
            return True
        else:
            return False

    def is_monthly(self):
        if self.is_daily() and self.time.tm_mday == 1:
            return True
        else:
            return False

    def is_yearly(self):
        if self.is_monthly() and self.time.tm_mon == 1:
            return True
        else:
            return False

    def remove(self):
        for file in self.files:
            os.remove(file)

    def __str__(self):
        return "%s in %s" % (self.files, self.base)


# loop through each dir in datadir
for dir in os.listdir(datadir):
    if dir.startswith('.'):
        # skip hidden directories
        continue
    if dir == 'lost+found':
        continue

    fullpath = os.path.normpath(datadir + '/' + dir)
    if not os.path.isdir(fullpath):
        print("Warning: %s: Not a directory." % fullpath)
        continue
    os.chdir(fullpath)

    backups = {}

    files = os.listdir('.')
    files.sort()

    for file in files:
        filestamp = file.split('.')[0]
        timestamp = ''
        try:
            timestamp = time.strptime(filestamp, timeformat)
        except ValueError as e:
            print('%s: %s' % (file, e))
            continue

        if timestamp not in list(backups.keys()):
            backups[timestamp] = backup(timestamp, fullpath, file)
        else:
            backups[timestamp].add(file)

    backup_items = sorted(backups.items(), key=lambda t: t[0])
    if last:  # NOTE: if last == 0, the slice returns an empty list!
        backup_items = backup_items[:-last]

    for stamp, bck in backup_items:
        bck = backups[stamp]
        bck_seconds = calendar.timegm(stamp)

        if bck_seconds > now - (hourly * 3600):
            continue

        if bck.is_daily() and bck_seconds > now - (daily * 86400):
            continue

        if bck.is_monthly() and bck_seconds > now - (monthly * 2678400):
            continue

        if bck.is_yearly() and bck_seconds > now - (yearly * 31622400):
            continue

        bck.remove()
