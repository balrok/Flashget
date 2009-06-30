#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import asyncore
import asynchat
import socket
import time
import thread


def get_api(data):
    # returns a tuple (is_error, X)
    # where X is the api-object or the errorstring when is_error was True
    parts = data.split('\n')
    if parts[0] != 'HELLO':
        return(True, 'first packet must be a HELLO-packet')
    api = ''
    for i in xrange(1, len(parts)):
        part = parts[i]
        if part.startswith('API'):
            api = part[5:]
        else:
            return (True, 'unhandled keyword in HELLO-packet keyword:"%s" whole packet:"%s"' % (part, data))
    if api == '':
        return (True, ' HELLO-packet needs to have the API-key')

    if api == '0.1':
        return (False, API_01())


class API(object):
    registered = {}

    @classmethod
    def register(cls, key, values, function):
        # this function gets called from inside the program
        # it lets the programmer register functions, which can be used from outside
        # key: will be the string which the client uses as keyword (for example GET_SPAM)
        # values: a dictionary with values as key and their default as value ({"PARAM1": None, "PARAM2":12})
        #   the default values also will be taken to transform stuff into int or string
        # function: a callback function, which should return a tuple (is_error, X) where X is either
        #   the errormsg or a dict with returnvalues
        if key in cls.registered:
            return False
        registered[key] = (values, function)
        return True

    @classmethod
    def error(cls, string):
        return ('ERROR', {'VAL': string})

    @classmethod
    def call(cls, key, values):
        # to lazy for documentation
        if key not in cls.registered:
            return error('%s is not available' % key)
        vals = cls.registered[key][0][:]                    # copy all default values - the loop will overwrite them
        id = 0
        if 'ID' in values:
            id = values['ID']
            del values['ID']

        for i in values:
            if i not in vals:
                return error('%s is no value in %s' % (i, key))
            v = values[i]
            if type(vals[i]) == int:
                try:
                    v = int(v)
                except:
                    return error('couldn\'t convert %s from %s to int' % (i, key))
            if type(vals[i]) == int:
                try:
                    v = float(v)
                except:
                    return error('couldn\'t convert %s from %s to float' % (i, key))
            vals[i] = v
        is_error, X = cls.registered[key][1](**vals)
        if is_error:
            return cls.error(X)
        else:
            X['ID'] = id
            return (key, X)


class API_01(API):
    def parse(self, data):
        parts = data.split('\n')
        key = parts[0]
        values = {}
        for i in xrange(1, len(parts)):
            x = parts[i].split(': ')
            values[x[0]] = x[1]
        ret_key, ret_values = API.call(key, values)
        return self.put_together(ret_key, ret_values)

    def put_together(self, key, value):
        tmp = []
        for i in value:
            tmp.append('%s: %s' % (i, value[i]))
        return '%s\n%s\x00\x00' % (key, '\n'.join(tmp))


class Service(asynchat.async_chat):

    def __init__(self, server, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator('\x00\x00')
        self.api = None
        self.data = ''
        self.server = server
        self.addr = addr

    def handle_close(self):
        self.server.handle_close(self.addr)
        self.close()

    def collect_incoming_data(self, data):
        self.data = self.data + data

    def found_terminator(self):
        print "Got data: \'%s\'" % self.data
        if not self.api:
            is_error, X = get_api(self.data)
            if is_error:
                print "hello-error %s" % X
                self.push(self.api.put_together('HELLO', {'ERROR': X}))
            else:
                self.api = X
                self.push(self.api.put_together('HELLO', {'ERROR': ''}))
        else:
            self.push(self.api.parse(self.data))
        self.push('Thanks for sending \'%s\'\r\n' % self.data)
        self.data = ''


class Dispatcher(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.connections = {}
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(3)

    def handle_close(self, addr):
        del self.connections[addr[1]]

    def handle_accept(self):
        sock, addr = self.accept()
        print 'accept connection %s' % repr(addr)
        serv_ice = Service(self, sock, addr)
        self.connections[addr[1]] = serv_ice

if __name__ == '__main__':
    try:
        disp = Dispatcher('localhost', 9090)
        print 'Serving ...'

        thread.start_new(asyncore.loop, ())
        print '... Server running'
        while True:
            time.sleep(2)
            print 'broadcast'
            for i in disp.connections:
                try:
                    disp.connections[i].push('hallo' + str(i))
                except e, err:
                    print e
                    print err

    except KeyboardInterrupt:
        print '\n',  KeyboardInterrupt
