from distutils.core import setup, Extension
import os

# define the extension module
cfuncs = Extension('cfuncs', sources=['cfuncs.c'])
ctrack = Extension('ctrack', sources=['ctrack.c'], extra_compile_args=["-Wunused-function"])

# run the setup
setup(ext_modules=[cfuncs, ctrack])

os.system("cp build/lib*/* .")
