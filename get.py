#!/usr/bin/python
# -*- coding: utf-8 -*-

import locale
import tools.commandline as commandline

locale.setlocale(locale.LC_ALL,"")

commandline.parse()
open('.flashget_log', 'a').write(commandline.get_log_line() + '\n')

import prog
from tools.log import setLogHandler
setLogHandler()
prog.main()
