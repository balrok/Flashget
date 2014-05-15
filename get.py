#!/usr/bin/python
# -*- coding: utf-8 -*-

import locale
import flashget.commandline as commandline
import flashget.log
flashget.log.dummy = 0

locale.setlocale(locale.LC_ALL, "")

commandline.parse()
open('.flashget_log', 'a').write(commandline.get_log_line() + '\n')

import prog
prog.main()
