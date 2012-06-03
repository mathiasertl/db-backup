from libdump import backend
import subprocess, os

class ejabberd(backend.backend):
    def get_db_list(self):
        return ['ejabberd']

    def get_command(self, database):
        path = os.path.normpath(self.section['ejabberd-base-dir'] + '/' + database + '.backup')
        return [ 'cat', path ]
        
    def prepare_db(self, database):
        cmd = [ 'ejabberdctl' ]
        if 'ejabberd-node' in self.section:
            cmd += [ '--node', self.section['ejabberd-node'] ]
        if 'ejabberd-auth' in self.section:
            cmd += ['--auth', self.section['ejabberd-auth'].split()]

        cmd += [ 'backup', database + '.backup' ]
        p = subprocess.Popen(cmd)
        p.communicate()

    def cleanup_db(self, database):
        path = os.path.normpath(self.section['ejabberd-base-dir'] + '/' + database + '.backup')
        os.remove(path)