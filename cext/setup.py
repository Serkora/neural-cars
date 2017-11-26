from distutils import sysconfig
from distutils.core import setup, Extension
import os

# define the extension module
cmodule = Extension('cmodule', include_dirs=["./"], sources=['common.c', 'track.c', 'sensors.c', 'neural.c', 'cmodule.c'])

cflags = sysconfig.get_config_var('CFLAGS')
opt = sysconfig.get_config_var('OPT')
sysconfig._config_vars['CFLAGS'] = cflags.replace(' -DNDEBUG ', ' ')
sysconfig._config_vars['OPT'] = opt.replace(' -DNDEBUG ', ' ')
cflags = sysconfig.get_config_var('CFLAGS')
opt = sysconfig.get_config_var('OPT')
#print(cflags, "\n\n\n", opt)
# run the setup
setup(ext_modules=[cmodule])

os.system("cp build/lib*/* .")
