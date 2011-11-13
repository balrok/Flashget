# vim: set fileencoding=utf-8 :

import sys, socket, time
from helper import *

socket.setdefaulttimeout(5)

from random import choice
import logging

log = logging.getLogger('main')

try:
    import config
except:
    class config:
        keepalive = True
        dns_reset = 60 * 60 * 8 # we cache dns->ip and after this time we will refresh our cacheentry

GZIP = True
try:
    import StringIO, gzip
except:
    GZIP = False

if 'MSG_WAITALL' in socket.__dict__:
    EASY_RECV = True
else:
    EASY_RECV = False

class http(object):
    conns = {} # this will store all keep-alive connections in form (host, state)
    dns_cache = {} # will translate host to ip ... 'dns_name.org': (ip, timestamp)
    host_page_port_cache = {} # cache for get_host_page_port this just avoids recalculation
    encoding = '' # when the url might have umlauts the encoding will convert it

    def __init__(self, url, log = None):
        cleanUrl = url.replace("\r","").replace("\n","").replace("\t","")
        self.origUrl = cleanUrl
        self.host, self.page, self.port = http.extract_host_page_port(cleanUrl)
        self.request = {}
        self.request['http_version'] = '1.1'
        self.request['method']       = 'GET'
        self.request['header']       = [] # can be set from outside
        self.post = ''
        if GZIP:
            self.request['header'].append('Accept-Encoding: gzip')
        self.log = log
        self.redirection = ''
        self.cookies = [] # list should later be a dict it's just my lazyness :/

    @classmethod
    def extract_host_page_port(cls, url, force = False):
        ''' returns tuple (host, page, port) force will avoid cache '''
        if not force:
            if url in cls.host_page_port_cache:
                return cls.host_page_port_cache[url]
        if url.startswith('http://'):                       # we don't need this
            url = url[7:]
        p  = url.find(':')                                  # port
        br = url.find('/')                                  # example.org:123/abc
        if br == -1:                                        # example.org:123?abc=1
            br = url.find('?')
            if br == -1:                                    # example.org:123
                br = len(url)
        if p != -1 and br > p:                              # br > p cause: example.org/bla=http://muh.org
            port = int(url[p+1:br])
            host = url[:p]
        else:
            port = 80
            host = url[:br]
        page = url[br:]
        if page == '':
            page = '/'
        page = page
        cls.host_page_port_cache[url] = (host, page, port)
        return (host, page, port)

    @classmethod
    def get_ip(cls, host, force = False):
        if not force and host in cls.dns_cache:
            ipList, last_update = cls.dns_cache[host]
            if last_update < time.time() + config.dns_reset:
                return cls.get_ip(host, True)
        else:
            ip, aliasList, ipList = socket.gethostbyname_ex(host)
            #ipList.append(ip)
            cls.dns_cache[host] = (ipList, time.time())
        if len(ipList) > 1:
            return choice(ipList)
        return ipList[0]

    def connect(self, force = False):
        if self.request['http_version'] == '1.1' and config.keepalive:
            self.keepalive = True
        else:
            self.keepalive = False
        if self.keepalive and not force:
            if self.host in http.conns and http.conns[self.host][0] == 'CONN_OPEN':
                return http.conns[self.host][1]
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.settimeout(10)
        try:
            self.ip = http.get_ip(self.host)
            c.connect((self.ip, self.port))
        except socket.timeout, (txt):
            if self.log:
                self.log.error('error in connect to %s:%d timeout: %s' % (self.host, self.port, txt))
            if self.host in http.conns:
                del http.conns[self.host]
            return None
        except socket.error, (e, txt):
            # socket.gaierror: (-2, 'Name or service not known')
            if self.log:
                self.log.error('error in connect to %s:%d errorcode:%d and %s' % (self.host, self.port, e, txt.decode('utf-8')))
            if self.host in http.conns:
                del http.conns[self.host]
            return None

        if self.keepalive:
            http.conns[self.host] = (c, 'CONN_IN_USE')
        return c

    def open(self, post = ''):
        if post:
            self.post = post

        self.c = self.connect()
        if not self.c:
            return
        header = []
        if self.post:
            self.request['method'] = 'POST'
        header.append('%s %s HTTP/%s' % (self.request['method'], self.page, self.request['http_version']))
        header.append('HOST: %s' % self.host)
        for i in self.request['header']:
            header.append(i)
        if self.post:
            if 'content_type' in self.request:
                header.append('Content-Type: %s' % self.request['content_type'])
            else:
                header.append('Content-Type: application/x-www-form-urlencoded')
            header.append('Content-Length: %d' % len(self.post))
            header.append('\r\n%s' % self.post)
        send = '\r\n'.join(header)
        if self.encoding:
            send = unicode(send).encode(self.encoding)
        if not self.post:
            send += '\r\n\r\n'
        self.c.sendall(send)
        try:
            self.get_head()
        except:
            self.log.error("error when receiving head")

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
        call = self.recv_blocking
        data += self.recv_with_reconnect_call(call, size)
        if precision:
            self.buf = data[size:]
            return data[:size]
        return data

    def recv_blocking(self, size = 4096):
        data = ''
        if EASY_RECV:
            data += self.c.recv(size, socket.MSG_WAITALL)
        else:
            while size > 0:
                chunk = self.c.recv(size)
                if chunk == '':
                    break
                data += chunk
                size -= len(chunk)
        return data

    def recv_with_reconnect_call(self, call, arg):
        ''' a wrapper around the socketrecv to allow reconnect on closed sockets '''
        try:
            return call(arg)
        except socket.timeout, (txt):
            if self.log:
                self.log.error('error in connect to %s:%d timeout: %s' % (self.host, self.port, txt))
            if self.host in http.conns:
                del http.conns[self.host]
            return None
        except socket.error, (e, err):
            # error: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgeset
            # gaierror: (-2,eerror: (104, 'Die Verbindung wurde vom Kommunikationspartner zur\xc3\xbcckgesetzt')
            if e == 104:
                self.c = self.connect(True)
                if not self.c:
                    return None
                return call(arg)
            else:
                if self.host in http.conns:
                    del http.conns[self.host] # we have a strange error here, so we just delete this host - cause it will surely produce more errors
                self.log.error('crecv has a problem with %d, %d, %s' % (e, err.eerror[0], err.eerror[1]))
        # return an empty sting in case of error
        return ''

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
        return ''

    def get_head(self):
        ''' just get the answering head - we need at least this, to receive the body (else we won't know if the body is chunked and so on)
        also returns all already gathered pieces of the body '''
        self.buf = None # reset it first (important)
        self.buf = self.recv_with_reconnect_call(self.c.recv, 4096)
        if self.buf is None:
            return None
        x = self.buf.find('\r\n\r\n')
        deadlockStop = 0
        lastData = ""
        while x == -1:
            deadlockStop+=1
            if deadlockStop == 23:
                self.log.error("stopping getHead.. Deadlock")
                return None
            data = self.recv()
            if data == lastData:
                self.log.error("stopping getHead.. receiving always the same")
                self.log.error((self.host, self.page))
                self.log.error(data)
                return None
            lastData = data
            self.buf += data
            x = self.buf.find('\r\n\r\n')
        self.head = header(self.buf[:x+2]) # keep the \r\n at the end, so we can search easier
        self.buf = self.buf[x+4:]
        if self.head.get('set-cookie'):
            self.cookies.append(self.head.get('set-cookie'))
        if self.keepalive:
            if self.head.get('connection') and self.head.get('connection') == 'close':
                if self.host in http.conns:
                    del http.conns[self.host]

        if self.head.status == 301 or self.head.status == 302 or self.head.status == 303: # 302 == found, 303 == see other
            if self.redirection == self.head.get('Location'):
                self.log.error("redirection loop")
            self.redirection = self.head.get('Location')
            if not self.redirection.startswith('http://'):
                self.redirection = 'http://'+self.host+self.redirection
            self.log.info("redirect "+self.origUrl+" -to-> "+self.redirection)
            self.host, self.page, self.port = http.extract_host_page_port(self.redirection)
            self.origUrl = self.redirection[:]
            self.open()

    def finnish(self):
        ''' when a download gets ended, this function will mark the connection as free for future requests '''
        if not self.c:
            return
        if self.keepalive:
            http.conns[self.host] = (self.c, 'CONN_OPEN')
        else:
            self.c.close()

    def get(self):
        if self.head.get('Transfer-Encoding') == 'chunked':
            body = self.get_chunks()
        else:
            length = self.head.get('Content-Length')
            if not length:
                length = 9999999 # very big - to make sure we download everything
                if self.log:
                    self.log.warning('there was no content length in the header')
                    self.log.warning(repr(self.head.plain))
            else:
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
        # when we delete this object, we can free the connection for future use
        if self.keepalive:
            if self.host in http.conns:
                if http.conns[self.host][1] != 'CONN_OPEN':
                    if self.log:
                        self.log.debug('creating a dirty connection')
                    self.finnish()


class header(object):
    def __init__(self, head):
        self.plain = head
        self.plain_lower = head.lower()
        # HTTP/1.0 200 OK
        # HTTP/1.0 300 Moved Permanently
        self.version = head[5:8]                            # 1.0
        self.status  = int(head[9:12])                      # 200
        x = head.find('\r')
        self.status_str  = head[13:x]                       # OK / permanently moved..
        self.cache = {}
        while True:
            y = head.find(':', x + 3) # + 3 is just a guess about the minlength of keywords
            if y == -1:
                break
            keyword = head[x+2:y].lower()
            x = head.find('\r', y + 3)
            value = head[y+2:x]
            self.cache[keyword] = value

    def get(self, what):
        what = what.lower()
        try:
            return self.cache[what]
        except:
            return None
    def __str__(self):
        return self.plain


if __name__ == '__main__':
    def tick_time(t):
        for i in xrange(0, t):
            time.sleep(3)
            print i

    a = http('http://dtwow.eu')
    a.request['header'].append('User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
    a.request['header'].append('Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    a.request['header'].append('Accept-Language: en-us,en;q=0.5')
    a.request['header'].append('Accept-Charset: utf-8,ISO-8859-1;q=0.7,*;q=0.7')
    a.open()
    a.get()
    #print a.head.plain()
    #print a.get()
    a = http('http://dtwow.eu')
    a.request['header'].append('User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
    a.request['header'].append('Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    a.request['header'].append('Accept-Language: en-us,en;q=0.5')
    a.request['header'].append('Accept-Charset: utf-8,ISO-8859-1;q=0.7,*;q=0.7')
    a.open()
    a.get()
    a.head.get('bla')
    a.head.get('bl1')
    a.head.get('bl2')
    a.head.get('bl3')
