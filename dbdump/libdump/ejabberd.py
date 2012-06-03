from libdump import backend
import subprocess, os

class ejabberd(backend.backend):
    def get_db_list(self):
        return [ 'ejabberd' ]

    def get_command(self, database):
        path = os.path.normpath(self.section['base-dir'] + '/' + database + '.backup')
        return [ 'cat', path ]
        
    def prepare_db(self, database):
        cmd = [ 'ejabberdctl' ]
        if 'node' in self.section:
            cmd += [ '--node', self.section['node'] ]
        if 'auth' in self.section:
            cmd += ['--auth', self.section['auth']]

        cmd += [ 'backup', database + '.backup' ]
        p = subprocess.Popen(cmd)
        p.communicate()

    def cleanup_db(self, database):
        path = os.path.normpath(self.section['base-dir'] + '/' + database + '.backup')
        os.remove(path)