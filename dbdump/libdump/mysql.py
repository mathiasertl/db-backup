"""
This file is part of dbdump.

Copyright 2009-2012 Mathias Ertl

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
import os, sys, stat

class mysql(backend.backend):

    @property
    def defaults(self):
        if 'mysql-defaults' in self.section:
            return os.path.expanduser(self.section['mysql-defaults'])
        if os.getuid() == 0 and os.path.exists('/etc/mysql/debian.cnf'):
            return '/etc/mysql/debian.cnf'
        return os.path.expanduser('~/.my.cnf')

    def prepare(self):
        if self.defaults and not os.path.exists(self.defaults):
            print("Error: %s: Does not exist." % self.defaults, file=sys.stderr)
            sys.exit(1)
        unsafe = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
        unsafe |= stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH

        mode = os.stat(self.defaults)[stat.ST_MODE]
        if mode & unsafe != 0:
            print("Warning: %s: unsafe permissions (fix with 'chmod go-rwx %s')"
                  % (self.defaults, self.defaults), file=sys.stderr)

    def get_db_list(self):
        excluded = ['information_schema', 'performance_schema']
        cmd = ['/usr/bin/mysql', '--defaults-file=%s' % self.defaults,
               '--execute=SHOW DATABASES', '-B', '-s']
        if self.args.verbose:
            print('%s # get list of databases' % ' '.join(cmd))
        p_list = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p_list.communicate()
        databases = stdout.decode().strip("\n").split("\n")
        p_list.wait()

        if p_list.returncode != 0:
            raise Exception("Unable to get list of databases: %s "
                % (stderr.decode().strip("\n")))

        return [ db for db in databases if db not in excluded ]

    def get_command(self, database):
        # get list of ignored tables:
        ignored_tables = self.section['mysql-ignore-tables'].split()
        ignored = [ t for t in ignored_tables if t.startswith("%s." % database) ]

        # assemble query for used engines in the database
        engine_query = "select ENGINE from information_schema.TABLES WHERE TABLE_SCHEMA='%s' AND ENGINE != 'MEMORY'"%database
        for table in ignored:
            engine_query += " AND TABLE_NAME != '%s'"%table.split('.')[1]
        engine_query += ' GROUP BY ENGINE'

        engine_cmd = [ 'mysql' ]
        if self.defaults:
            engine_cmd.append('--defaults-file=%s' % self.defaults)
        engine_cmd += [ '-NB', "--execute=%s" % engine_query ]

        if self.args.verbose:
            print('%s # get list of database engines' % ' '.join(engine_cmd))
        p = Popen(engine_cmd, stdout=PIPE)
        types = p.communicate()[0].decode('utf-8').strip().split("\n")

        cmd = [ 'mysqldump' ]
        if self.defaults:
            cmd.append('--defaults-file=%s' % self.defaults)

        for table in ignored:
            cmd.append('--ignore-table="%s"' % table)

        if types == [ 'InnoDB' ]:
            cmd += ['--single-transaction', '--quick']
        else:
            cmd.append('--lock-tables')

        cmd += [ '--comments', database ]
        return cmd
