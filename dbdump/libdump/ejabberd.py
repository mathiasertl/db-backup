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

import os
import subprocess

from libdump import backend


class ejabberd(backend.backend):
    def get_db_list(self):
        return ['ejabberd']

    def get_command(self, database):
        path = os.path.normpath(os.path.join(
            self.section['ejabberd-base-dir'], '%s.dump' % database))
        return ['cat', path]

    def prepare_db(self, database):
        cmd = ['ejabberdctl']
        if 'ejabberd-node' in self.section:
            cmd += ['--node', self.section['ejabberd-node']]
        if 'ejabberd-auth' in self.section:
            cmd += ['--auth', self.section['ejabberd-auth'].split()]

        cmd += ['dump', '%s.dump' % database]
        if self.args.verbose:
            print('%s # prepare db' % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.communicate()

    def cleanup_db(self, database):
        path = os.path.normpath(os.path.join(
            self.section['ejabberd-base-dir'], '%s.dump' % database))
        if self.args.verbose:
            print('rm %s # remove local dump' % path)
        os.remove(path)
