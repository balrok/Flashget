#!/usr/bin/env python

import select
import socket
import sys
from tools.helper import textextract
from tools.cache import Cache
import config
import pickle


caches = {}

host = 'localhost'
port = config.cachePort
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host,port))
server.listen(socket.SOMAXCONN)
input = [server,sys.stdin]
running = 1
flush = 0
while running:
    inputready,outputready,exceptready = select.select(input,[],[])

    for s in inputready:
        flush += 1
        if flush == 1:
            flush = 0
            sys.stdout.flush()

        if s == server:
            # handle the server socket
            client, address = server.accept()
            input.append(client)

        elif s == sys.stdin:
            # handle standard input
            junk = sys.stdin.readline()
            running = 0
        else:
            # handle all other sockets
            try:
                size = s.recv(8).rstrip()
                if not size:
                    s.close()
                    input.remove(s)
                    continue

                size = int(size)
                origSize = int(size)
                data = ''
                while size > 0:
                    chunk = s.recv(size)
                    if chunk == '':
                        raise socket.error("ERROR chunk empty but not full size retrieved")
                    data += chunk
                    size -= len(chunk)

                data = pickle.loads(data)

                command = data['c']
                key = data['k']
                directory = data['d']
                value = data['v']
                section = data['section']
                if directory not in caches:
                    caches[directory] = Cache(directory)
                cache = caches[directory]
                cache.key = key
                if command == 'lookup':
                    print "l",
                    sendData = cache.lookup(section)
                    sendData = pickle.dumps(sendData, 1)
                    size = str(len(sendData))
                    size += (8-len(size))*" "
                    s.sendall(size+sendData)
                elif command == 'allkeys':
                    print ""
                    print "looking up all keys: this can take a while.."
                    sendData = cache.allkeys(section)
                    print "got"
                    sendData = pickle.dumps(sendData, 1)
                    size = str(len(sendData))
                    size += (8-len(size))*" "
                    s.sendall(size+sendData)
                    print "sent"
                elif command == 'write':
                    print "w",
                    #print "writing in: "+key+"/"+section+ ".. data: "+value[:100]
                    cache.write(section, value)
                elif command == 'remove':
                    print "r",
                    cache.remove(section)
            except socket.error, e:
                print "socket error "+str(e)
                s.close()
                input.remove(s)


server.close()
