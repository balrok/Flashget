#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import locale
import tools.commandline as commandline

locale.setlocale(locale.LC_ALL,"")

commandline.parse()
open('.flashget_log', 'a').write(' '.join(sys.argv) + '\n')

import prog
from tools.log import setLogHandler
setLogHandler()
prog.main()
