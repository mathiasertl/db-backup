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

import shlex
import os
from subprocess import Popen, PIPE


class backend(object):
    def __init__(self, section, args):
        self.args = args
        self.section = section
        self.base = section['datadir']
        if 'sign-key' in section or 'recipient' in section:
            self.gpg = True
        else:
            self.gpg = False

    def make_su(self, cmd):
        if 'su' in self.section:
            cmd = ['su', self.section['su'], '-s',
                   '/bin/bash', '-c', ' '.join(cmd)]
        return cmd

    def get_ssh(self, path, cmds):
        cmds = [' '.join(cmd) for cmd in cmds]
        prefix = 'umask 077; mkdir -m 0700 -p %s; ' % os.path.dirname(path)
        ssh_cmd = prefix + ' | '.join(cmds) + ' > %s.sha1' % path

        ssh = ['ssh']
        timeout = self.section['ssh-timeout']
        if timeout:
            ssh += ['-o', 'ConnectTimeout=%s' % timeout, ]

        opts = self.section['ssh-options']
        if opts:
            ssh += shlex.split(opts)

        ssh += [self.section['remote'], ssh_cmd]

        return ssh

    def dump(self, db, timestamp):
        cmd = self.make_su(self.get_command(db))
        if not cmd:
            return

        dirname = os.path.abspath(os.path.join(self.base, db))
        path = os.path.join(dirname, '%s.gz' % timestamp)
        if self.gpg:
            gpg = ['gpg']
            if 'sign_key' in self.section:
                gpg += ['-s', '-u', self.section['sign-key']]
            if 'recipient' in self.section:
                gpg += ['-e', '-r', self.section['recipient']]
            path += '.gpg'

        gzip = ['gzip', '-f', '-9', '-', '-']
        tee = ['tee', path]
        sha1sum = ['sha1sum']
        sed = ['sed', 's/-$/%s/' % os.path.basename(path)]

        if 'remote' in self.section:
            ssh = self.get_ssh(path, [tee, sha1sum, sed])

            cmds = [cmd, gzip, ]  # just for output
            p_dump = Popen(cmd, stdout=PIPE)
            p_gzip = Popen(gzip, stdin=p_dump.stdout, stdout=PIPE)
            ssh_stdin = p_gzip.stdout  # what to pipe into SSH
            if self.gpg:
                p_gpg = Popen(gpg, stdin=p_gzip.stdout, stdout=PIPE)
                ssh_stdin = p_gpg.stdout
                cmds.append(gpg)

            cmds.append(ssh)
            if self.args.verbose:
                str_cmds = [' '.join(c) for c in cmds]
                print('# Dump databases:')
                print(' | '.join(str_cmds))

            p_ssh = Popen(ssh, stdin=ssh_stdin, stdout=PIPE)
            p_ssh.communicate()
            if p_ssh.returncode == 255:
                raise RuntimeError("SSH returned with exit code 255.")
            elif p_ssh.returncode != 0:
                raise RuntimeError("%s returned with exit code %s."
                                   % (ssh, p_ssh.returncode))
        else:
            if not os.path.exists(dirname):
                os.mkdir(dirname, 0o700)

            f = open(path + '.sha1', 'w')
            cmds = [cmd, gzip, ]  # just for output
            p_dump = Popen(cmd, stdout=PIPE)
            p_gzip = Popen(gzip, stdin=p_dump.stdout, stdout=PIPE)
            tee_pipe = p_gzip.stdout
            if self.gpg:
                p_gpg = Popen(gpg, stdin=p_dump.stdout, stdout=PIPE)
                tee_pipe = p_gpg.stdout
                cmds.append(gpg)

            p_tee = Popen(tee, stdin=tee_pipe, stdout=PIPE)
            p_sha1 = Popen(sha1sum, stdin=p_tee.stdout, stdout=PIPE)
            p_sed = Popen(sed, stdin=p_sha1.stdout, stdout=f)

            cmds += [tee, sha1sum, sed]
            if self.args.verbose:
                str_cmds = [' '.join(c) for c in cmds]
                print('# Dump databases:')
                print(' | '.join(str_cmds))

            p_sed.communicate()
            f.close()

    def prepare(self):
        pass

    def prepare_db(self, database):
        pass

    def cleanup_db(self, database):
        pass

    def cleanup(self):
        pass
