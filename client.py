#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import socket, time
coon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
coon.connect(('localhost', 9090))




msg = 'HELLO\nAPI: 0.1'
coon.send(msg + '\x00\x00')

while True:
    print coon.recv(100)
    time.sleep(1)
msg = 'ADD_PAGE\nVALUE: http://bla.org\nCALLBACK: stream nr 1'
# -> RESPONSE
# 'ADDED_PAGE\nCALLBACK: stream nr 1\n LINKS: 12\nTITLE: blabla 123'
msg = 'GET_PAGE_LIST'
# -> RESPONSE
# 'PAGE_LIST\nSTREAM1: http://bla.org\nCALLBACK1: stream nr 1'
msg = 'GET_STREAM_LIST\nPAGE: stream nr 1'
# -> RESPONSE
# 'STREAM_LIST\nPAGE: stream nr j:q
# ï1
msg = 'D_STREAM\nVALUE: http://bla.org'
coon.close()
