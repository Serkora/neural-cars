from distutils.core import setup, Extension
import os

# define the extension module
cfuncs = Extension('cfuncs', sources=['cfuncs.c'])
cmodule = Extension('cmodule', include_dirs=["./"], sources=['common.c', 'track.c', 'sensors.c', 'neural.c', 'cmodule.c'])

# run the setup
setup(ext_modules=[cfuncs, cmodule])

os.system("rm *.so")
os.system("cp build/lib*/* .")
