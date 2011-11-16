#!/usr/bin/env python

import select
import socket
import sys
from tools.helper import textextract
from tools.cache import KyotoCache as Cache
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
while running:
    inputready,outputready,exceptready = select.select(input,[],[])

    for s in inputready:
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
                    break
                data += chunk
                size -= len(chunk)
            try:
                data = pickle.loads(data)
            except:
                # this means data was not fully received
                print origSize
                print size
                print len(data)
                print data[:1000]
                print "^error"
                # find out if it was a lookup command then we have to respond
                if data.find('lookup') > 0:
                    sendData = pickle.dumps('')
                    size = str(len(sendData))
                    size += (8-len(size))*" "
                    s.send(size+sendData)
                continue

            command = data['c']
            key = data['k']
            directory = data['d']
            value = data['v']
            section = data['section']
            #print (origSize, command, key, directory, value[:100])
            if directory not in caches:
                caches[directory] = Cache(directory)
            cache = caches[directory]
            cache.key = key
            if command == 'lookup':
                print "l",
                #print "looking up: "+key
                sendData = cache.lookup(section)
                #if not sendData:
                #    print "not found"
                #else:
                #    print "found"
                sendData = pickle.dumps(sendData)
                size = str(len(sendData))
                size += (8-len(size))*" "
                s.send(size+sendData)
            if command == 'write':
                print "w",
                #print "writing in: "+key+"/"+section+ ".. data: "+value[:100]
                cache.write(section, value)
            if command == 'remove':
                print "r",
                cache.remove(section)

server.close()
