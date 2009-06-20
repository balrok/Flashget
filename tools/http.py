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


C_OPEN   = 1
C_IN_USE = 2
class http(object):
    conns = {} # this will store all keep-alive connections in form (host, state)
    dns_cache = {} # will translate host to ip ... 'dns_name.org': (ip, timestamp)
    host_page_port_cache = {} # cache for get_host_page_port this just avoids recalculation

    def __init__(self, url, log = None):
        self.host, self.page, self.port = http.extract_host_page_port(url)
        self.request = {}
        self.request['http_version'] = '1.1'
        self.request['method']       = 'GET'
        self.request['header']       = [] # can be set from outside
        if GZIP:
            self.request['header'].append('Accept-Encoding: gzip')
        self.log = log
        self.redirection = ''

    @classmethod
    def extract_host_page_port(cls, url, force = False):
        ''' returns tuple (host, page, port) '''
        if not force and url in cls.host_page_port_cache:
            return host_page_port_cache[url]
        page = ''
        if url.startswith('http://'): # we don't need this
            url = url[7:]
        p = url.find(':')   # port
        br = url.find('/')  # get request
        if br < p: # cause things like example.org:123/bla=http://muh.org are possible
            p = -1
        if br == -1:
            br = url.find('?') # get request 2
        if br == -1:
            host = url
            page = '/'
            br = 999999
        else:
            host = url[:br]
            page = url[br:]
        port = 80
        if p != -1:
            port = int(url[p+1:br])
            host = url[:p]
        cls.host_page_port_cache[url] = (host, page, port)
        return (host, page, port)

    @classmethod
    def get_ip(cls, host, force = False):
        if force or host not in cls.dns_cache:
            ip = socket.gethostbyname(host)
            cls.dns_cache[host] = (ip, time.time())
        else:
            ip, last_update = cls.dns_cache[host]
            if last_update < time.time() + (60 * 60 * 8): # after 8h
                ip = cls.get_ip(host, True)
        return ip

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
            self.ip = http.get_ip(self.host)
            c.connect((self.ip, self.port))
        except socket.gaierror, (e, txt):
            # socket.gaierror: (-2, 'Name or service not known')
            if self.log:
                self.log.bug('error in connect to %s:%d errorcode:%d and %s' % (self.host, self.port, e, txt.decode('utf-8')))
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
            if 'content_type' in self.request:
                header.append('Content-Type: %s' % self.request['content_type'])
            else:
                header.append('Content-Type: application/x-www-form-urlencoded')
            header.append('Content-Length: %d' % len(post))
            header.append('\r\n%s' % post)
        send = '\r\n'.join(header)
        if not post:
            send += '\r\n\r\n'
        self.c.sendall(send)
        self.get_head()

    def recv(self, size = 4096, precision = False):
        ''' a blocking recv function - which should also work on windows and solaris
            this is the lowest level of recv, which i can call from this class '''
        data = ''
        if self.buf:
            data = self.buf[:size]
            self.buf = self.buf[size:]
            size -= len(data)
            if size == 0:
                return data
        if EASY_RECV:
            data += self.c.recv(size, socket.MSG_WAITALL)
        else:
            while size > 0:
                chunk = self.c.recv(size)
                if chunk == '':
                    break
                data += chunk
                size -= len(chunk)
        if precision:
            self.buf = data[size:]
            return data[:size]
        return data

    def recv_with_reconnect(self, size = 4096):
        ''' a wrapper around the socketrecv to allow reconnect on closed sockets '''
        try:
            return self.c.recv(size)
        except socket.error, (e, err):
            # error: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgeset
            # gaierror: (-2,eerror: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgesetzt')
            if e == 104:
                self.c = self.connect(True)
                return self.c.recv(size)
            else:
                if self.host in http.conns:
                    del http.conns[self.host] # we have a strange error here, so we just delete this host - cause it will surely produce more errors
                self.log.bug('crecv has a problem with %d, %d, %s' % (e, err.eerror[0], err.eerror[1]))

    def get_chunks(self):
        ''' getting chunks - through some strange implementation, i will first recv everything and then just strip off the chunk-informations '''
        # TODO implement it better - currently it is quite slow
        body = self.buf
        # first we download the whole file
        while True:
            if body.endswith('\n0\r\n\r\n'):
                break
            body += self.c.recv(4096)
        body = body[:-5]

        # after that we create a new return string and eliminate all chunk-trash
        x = body.find('\r\n')
        body2 = ''
        while x > 0:
            length = int(body[:x], 16)
            body2 += body[(x + 2):(x + 2 + length)]
            body = body[x + 4 + length:]
            if not body:
                return body2
            x = body.find('\r\n')
        # self.log.bug('strange chunked response')
        return ''

    def get_head(self):
        ''' just get the answering head - we need at least this, to receive the body (else we won't know if the body is chunked and so on)
        also returns all already gathered pieces of the body '''
        self.buf = None # reset it first (important)
        self.buf = self.recv_with_reconnect()
        x = self.buf.find('\r\n\r\n')
        while x == -1:
            self.buf += self.recv()
            x = self.buf.find('\r\n\r\n')
        self.head = header(self.buf[:x+2]) # keep the \r\n at the end, so we can search easier
        self.buf = self.buf[x+4:]
        if self.head.status == 301 or self.head.status == 302 or self.head.status == 303: # 302 == found, 303 == see other
            self.redirection = self.head.get('Location')
            self.host, self.page, self.port = http.extract_host_page_port(self.redirection)
            self.open()

    def finnish(self):
        ''' when a download gets ended, this function will mark the connection as free for future requests '''
        if self.keepalive:
            http.conns[self.host] = (self.c, C_OPEN)
        else:
            self.c.close()

    def get(self):
        if self.head.get('Transfer-Encoding') == 'chunked':
            body = self.get_chunks()
        else:
            length = self.head.get('Content-Length')
            if not length:
                length = self.head.get('Content-length') # HACK: in general those headers are case insensitive
                if not length:
                    length = 9999999 # very big - to make sure we download everything
                    if self.log:
                        self.log.warning('there was no content length in the header')
                        self.log.warning(repr(self.head.plain()))
            length = int(length)
            # if delta > 0: - i think this isn't needed
            body = self.recv(length)

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
        # -> i tested it with google and it seems ok
        if self.keepalive:
            if self.host in http.conns and http.conns[self.host][1] != C_OPEN:
                if self.log:
                    self.log.debug('creating a dirty connection')
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
