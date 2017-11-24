from distutils.core import setup, Extension
import os

# define the extension module
cmodule = Extension('cmodule', include_dirs=["./"], sources=['common.c', 'track.c', 'sensors.c', 'neural.c', 'cmodule.c'])

# run the setup
setup(ext_modules=[cmodule])

os.system("cp build/lib*/* .")
