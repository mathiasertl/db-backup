"""
This file is part of dbdump.

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

import os, time
from subprocess import *

class backend():
    def __init__(self, options):
        self.options = options
        self.base = options.datadir
        if self.options.sign_key or self.options.recipient:
            self.gpg = True
        else:
            self.gpg = False

    def make_su(self, cmd):
        if self.options.su:
            cmd = [ 'su', self.options.su, '-s', '/bin/bash', '-c', ' '.join(cmd) ]
        return cmd

    def get_ssh(self, path, cmds):
        cmds = [ ' '.join(cmd) for cmd in cmds ]
        opts = self.options.remote.split()
        prefix = 'umask 077; mkdir -m 0700 -p %s; ' %(os.path.dirname(path))
        ssh_cmd = prefix + ' | '.join(cmds) + ' > %s.sha1' %(path)
        test = [ 'ssh' ] + opts + [ ssh_cmd ]
        return test

    def dump(self, db, timestamp):
        cmd = self.make_su(self.get_command(db))

        dirname = os.path.normpath(self.base + '/' + db)
        path = os.path.normpath(dirname + '/' + timestamp)
        if self.gpg:
#            gpg = [ 'gpg', '-ser', self.options.gpg, '-' ]
            gpg = [ 'gpg' ]
            if self.options.sign_key:
                gpg += [ '-s', '-u', self.options.sign_key ]
            if self.options.recipient:
                gpg += [ '-e', '-r', self.options.recipient ]
            path += '.gpg'
                
        path += '.gz'

        gzip = [ 'gzip', '-f', '-9', '-', '-' ]
        tee = [ 'tee', path ]
        sha1sum = [ 'sha1sum' ]
        sed = [ 'sed', 's/-$/%s/' %(os.path.basename(path)) ]

        if self.options.remote:
            ssh = self.get_ssh(path, [gzip, tee, sha1sum, sed])

            p1 = Popen(cmd, stdout=PIPE)
            p = p1
            if self.gpg:
                p = Popen(gpg, stdin=p1.stdout, stdout=PIPE)

            p2 = Popen(ssh, stdin=p.stdout, stdout=PIPE)
            output = p2.communicate()[0]
            if p2.returncode == 255:
                raise RuntimeError("SSH returned with exit code 255.")
            elif p2.returncode != 0:
                raise RuntimeError("%s returned with exit code %s."%(ssh, p2.returncode))
        else:   
            if not os.path.exists(dirname):
                os.mkdir(dirname, 0o700)

            f = open(path + '.sha1', 'w')
            p1 = Popen(cmd, stdout=PIPE)
            p = p1
            if self.gpg:
                p = Popen(gpg, stdin=p1.stdout, stdout=PIPE)
            p2 = Popen(gzip, stdin=p1.stdout, stdout=PIPE)
            p3 = Popen(tee, stdin=p2.stdout, stdout=PIPE)
            p4 = Popen(sha1sum, stdin=p3.stdout, stdout=PIPE)
            p5 = Popen(sed, stdin=p4.stdout, stdout=f)
            p5.communicate()
            f.close()
    
    def prepare(self):
        pass

    def prepare_db(self, database):
        pass

    def cleanup_db(self, database):
        pass

    def cleanup(self):
        pass
