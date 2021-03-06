#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import sys
import io

import flashget

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'flashget',
    'flashget.pages',
    'flashget.streams',
]


with io.open('readme.md') as f:
    readme = f.read()
with io.open('history.md') as f:
    history = f.read()
with io.open("requirements.txt") as f:
    requires = [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#')]


setup(
    name='flashget',
    version=flashget.__version__,
    description='Flash downloader.',
    long_description=readme + '\n\n' + history,
    author='Carl Schönbach',
    author_email='carl.schoenbach@gmail.com',
    url='https://github.com/balrok/Flashget',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'flashget': 'flashget'},
    # scripts = ['get.py'],
    entry_points = {
        'console_scripts': [
            'flashget = flashget.main:main',
        ],
        'gui_scripts': [
            'flashget_gui = flashget.main:gui',
        ],
    },
    include_package_data=True,
    install_requires=requires,
    license='MIT',
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: File Sharing',
        'Topic :: Home Automation',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
