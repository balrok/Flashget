# I took this code from web2py - for example:
# https://raw.githubusercontent.com/web2py/web2py/f5f6f365f9908c1c98cc6a5b7086568befa23be9/gluon/tests/test_cache.py

import sys
import os

def fix_sys_path():
    """
    logic to have always the correct sys.path
     '', flashget/flashget, flashget/ ...
     (The code is from web2py project)
    """

    def add_path_first(path):
        sys.path = [path] + [p for p in sys.path if (
            not p == path and not p == (path + '/'))]


    path = os.path.dirname(os.path.abspath(__file__))

    if not os.path.isfile(os.path.join(path,'get.py')):
        i = 0
        while i<10:
            i += 1
            if os.path.exists(os.path.join(path,'get.py')):
                break
            path = os.path.abspath(os.path.join(path, '..'))

    paths = [path,
             os.path.abspath(os.path.join(path, 'flashget')),
             '']
    [add_path_first(x) for x in paths]

oldcwd = None
def setUpModule():
    global oldcwd
    if oldcwd is None:
        oldcwd = os.getcwd()
        if not os.path.isdir('flashget'):
            os.chdir(os.path.realpath('../'))
def tearDownModule():
    global oldcwd
    if oldcwd:
        os.chdir(oldcwd)
        oldcwd = None
