# This file is part of dbdump (https://github.com/mathiasertl/db-backup).
#
# dbdump is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# dbdump is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with dbdump. If not,
# see <http://www.gnu.org/licenses/>.

from subprocess import PIPE
from subprocess import Popen

from libdump import backend


class postgresql(backend.backend):
    def get_db_list(self):
        cmd = ['psql', '-Aqt', '-c', 'select datname from pg_database']

        if 'postgresql-psql-opts' in self.section:
            cmd += self.section['postgresql-psql-opts'].split(' ')

        if 'postgresql-connectstring' in self.section:
            cmd.append(self.section['postgresql-connectstring'])

        if 'su' in self.section:
            quoted_args = [f"\"{arg}\"" if ' ' in arg else arg for arg in cmd ]
            cmd = ['su', self.section['su'], '-s', '/bin/bash', '-c',
                   ' '.join(quoted_args)]

        p_list = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p_list.communicate()
        databases = [line for line in stdout.decode().strip().split("\n")
                     if line != 'template0']

        p_list.wait()
        if p_list.returncode != 0:
            raise Exception("Unable to get list of databases: %s "
                            % (stderr.decode().strip("\n")))

        return databases

    def get_command(self, database):
        cmd = ['pg_dump', '-c']
        if 'postgresql-pgdump-opts' in self.section:
            cmd += self.section['postgresql-pgdump-opts'].split(' ')

        connectstring_options = []
        if 'postgresql-connectstring' in self.section:
            connectstring_options = self.section['postgresql-connectstring'].split(' ')

        connectstring_options.append(f"dbname={database}")
        cmd.append(' '.join(connectstring_options))

        return cmd
