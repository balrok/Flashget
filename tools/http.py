# vim: set fileencoding=utf-8 :

import sys, socket, time
from helper import *
import config

GZIP = True
try:
    import StringIO, gzip
except:
    GZIP = False

if 'MSG_WAITALL' in socket.__dict__:
    EASY_RECV = True
else:
    EASY_RECV = False

def extract_host_page(url):
    ''' returns tuple (host, page) '''
    if url.startswith('http://'):
        url = url[7:]
    br = url.find('/')
    if br == -1:
        host = url
        page = '/'
    else:
        host = url[:br]
        page = url[br:]
    return (host, page)


C_OPEN   = 1
C_IN_USE = 2
class http(object):
    conns = {} # this will store all keep-alive connections in form (host, state)

    def __init__(self, url, log = None):
        self.host, self.page = extract_host_page(url)
        self.port       = 80
        self.request = {}
        self.request['http_version'] = '1.1'
        self.request['method']       = 'GET'
        self.request['header']       = [] # can be set from outside
        if GZIP:
            self.request['header'].append('Accept-Encoding: gzip')
        self.log = log
        self.buf = None

    def connect(self, force = False):
        if self.request['http_version'] == '1.1' and config.keepalive:
            self.keepalive = True
        else:
            self.keepalive = False
        if self.keepalive and self.host in http.conns and not force:
            if http.conns[self.host][0] == C_OPEN:
                return http.conns[self.host][1]
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            c.connect((self.host, self.port))
        except socket.gaierror, (e, txt):
            # socket.gaierror: (-2, 'Name or service not known')
            self.log.bug('error in connect to %s:%d errorcode:%d and %s' % (self.host, self.port, e, txt))
            if self.host in http.conns:
                del http.conns[self.host]
        else:
            if self.keepalive:
                http.conns[self.host] = [c, C_IN_USE]
        return c

    def open(self, post = ''):
        self.c = self.connect()
        header = []
        if post:
            self.request['method'] = 'POST'
        header.append('%s %s HTTP/%s' % (self.request['method'], self.page, self.request['http_version']))
        header.append('HOST: %s' % self.host)
        for i in self.request['header']:
            header.append(i)
        if post:
            header.append('Content-Type: application/x-www-form-urlencoded')
            header.append('Content-Length: %d' % len(post))
            header.append('\r\n%s' % post)
        send = '\r\n'.join(header)
        if not post:
            send += '\r\n\r\n'
        self.c.sendall(send)
        self.get_head()

    def recv(self, size):
        ''' a blocking recv function - which should also work on windows and solaris
            this is the lowest level of recv, which i can call from this class '''
        if EASY_RECV:
            data = self.crecv(size, socket.MSG_WAITALL)
        else:
            data = ''
            while True:
                chunk = self.crecv(size)
                if chunk == '':
                    break
                data += chunk
        if self.buf:
            data = self.buf + data
            self.buf = None
        return data

    def crecv(self, size = 4096, args = None):
        ''' a wrapper around the socketrecv to allow reconnect on closed sockets '''
        try:
            if args:
                return self.c.recv(size, args)
            else:
                return self.c.recv(size)
        except error, (e, err):
            # error: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgeset
            # gaierror: (-2,eerror: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgesetzt')
            if err.eerror[0] == 104:
                self.c = self.connect(True)
                if args:
                    return self.c.recv(size, args)
                else:
                    return self.c.recv(size)
            else:
                if self.host in http.conns:
                    del http.conns[self.host] # we have a strange error here, so we just delete this host - cause it will surely produce more errors
                self.log.bug('crecv has a problem with %d, %d, %s' % (e, err.eerror[0], err.eerror[1]))

    def get_chunks(self, body, to_end = True):
        ''' recursively getting chunks to_end is an internally used bool, to determine if we received already the full body '''
        if to_end: # first we download the whole file
            while True:
                if body.endswith('\n0\r\n\r\n'):
                    break
                body += self.crecv()
            body = body[:-5]

        # after that we create a new return string and eliminate all chunk-trash
        x = body.find('\r\n')
        if x > 0:
            length = int(body[:x], 16)
            ret = body[(x + 2):(x + 2 + length)]
            next = body[x + 2 + length:]
            if not next[2:]:
                return ret
            return ret + self.get_chunks(next[2:], False)
        else:
            # self.log.bug('strange chunked response')
            return ''

    def get_head(self):
        # TODO add a nonblocking recv here, cause we can be quite sure, that after the recv we want to read at least the return-header
        # maybe make an argument, here
        # TODO check for keep-alive here
        ''' just get the answering head - we need at least this, to receive the body (else we won't know if the body is chunked and so on)
        also returns all already gathered pieces of the body '''
        buf = ''
        while True:
            buf += self.crecv() # don't use self.recv here - else it would break the chunked transfer
            x = buf.find('\r\n\r\n')
            if x != -1:
                self.buf = buf[x+4:]
                break
        self.head = header(buf[:x+2]) # keep the \r\n at the end, so we can search easier
        if self.head.status == 301 or self.head.status == 302 or self.head.status == 303: # 302 == found, 303 == see other
            self.redirection = self.head.get('Location')
            self.host, self.page = extract_host_page(self.redirection)
            self.open()
        # open(self.host,'w').writelines(self.head.plain())


    def finnish(self):
        ''' when a download gets ended, this function will mark the connection as free for future requests '''
        if self.keepalive:
            http.conns[self.host] = (self.c, C_OPEN)
        else:
            self.c.close()

    def get(self):
        body = ''

        if self.head.get('Transfer-Encoding') == 'chunked':
            body = self.get_chunks(self.buf)
        else:
            # http://code.activestate.com/recipes/408859/
            # for recv-all ideas - i use the simple method where i expect the server to close - merged with the content-length field
            body = body
            length = self.head.get('Content-Length')
            if not length:
                length = 9999999 # very big - to make sure we download everything
            else:
                length = int(length)
            downloaded = len(body)
            body += self.recv(length - downloaded)

        self.finnish() # close connection or free it for future requests

        if GZIP and self.head.get('Content-Encoding') == 'gzip':
            compressedstream = StringIO.StringIO(body)
            gzipper   = gzip.GzipFile(fileobj = compressedstream)
            body = gzipper.read()
        return body

    def get_redirection(self):
        if self.redirection:
            return self.redirection
        return ''

    def __del__(self):
        # TODO - look if this is realy ok.. for instance someone could request just the header and ignore the body part
        # i don't know what happens if the next download will reuse this connection, where the body-part is still in
        if http.conns[self.host][1] != C_OPEN:
            self.log.warning('creating a dirty connection')
            self.finnish()


class header(object):
    def __init__(self, head):
        self.head = head
        # HTTP/1.0 200 OK
        self.version = head[5:8] # 1.0
        self.status  = int(head[9:12]) # 200
        self.cached = {}
    def get(self, what):
        if what not in self.cached:
            self.cached[what] = textextract(self.head, what + ': ', '\r\n')
        return self.cached[what]
    def plain(self):
        return self.head

if __name__ == '__main__':
    def tick_time(t):
        for i in xrange(0, t):
            time.sleep(1)
            print i

    a = http('http://dtwow.eu')
    a.header.append('User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
    a.header.append('Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    a.header.append('Accept-Language: en-us,en;q=0.5')
    a.header.append('Accept-Charset: utf-8,ISO-8859-1;q=0.7,*;q=0.7')
    a.open()
    a.get()
    #print a.head.plain()
    #print a.get()
    tick_time(270)
    a = http('http://dtwow.eu')
    a.header.append('User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
    a.header.append('Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    a.header.append('Accept-Language: en-us,en;q=0.5')
    a.header.append('Accept-Charset: utf-8,ISO-8859-1;q=0.7,*;q=0.7')
    a.open()
    print a.get()
