# vim: set fileencoding=utf-8 :

import sys, socket, time
from helper import *

GZIP = True
try:
    import StringIO, gzip
except:
    GZIP = False


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


class http(object):
    def __init__(self, url, log = None):
        self.host, self.page = extract_host_page(url)
        self.port       = 80
        self.request = {}
        self.request['http_version'] = '1.0'
        self.request['method']       = 'GET'
        self.request['header']       = [] # can be set from outside
        if GZIP:
            self.request['header'].append('Accept-Encoding: gzip')
        self.header = []
        self.log = log

    def connect(self):
        # TODO maybe try to implement a keepalive here
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((self.host, self.port))
        return c

    def open(self, post = ''):
        self.c = self.connect()
        header = []
        if post:
            self.request['method'] = 'POST'
        header.append(self.request['method']+ ' ' + self.page + ' HTTP/' + self.request['http_version'])
        header.append('HOST: ' + self.host)
        for i in self.request['header']:
            header.append(i)
        header.append('Conection: close')
        if post:
            header.append('Content-Type: application/x-www-form-urlencoded')
            header.append('Content-Length: ' + str(len(post)))
            header.append('\r\n' + post)
        send = '\r\n'.join(header)
        if not post:
            send += '\r\n\r\n'
        self.c.sendall(send)
        self.get_head()

    def get_chunks(self, body):
        while True:
            x = body.find('\r\n')
            if x>0:
                self.body += body[x+2:]
            else:
                self.body += body
            if self.body[-5:] == '0\r\n\r\n':
                self.body = self.body[:-5]
                break
            body = self.c.recv(40960)
        return body

    def get_head(self):
        # TODO add a nonblocking recv here, cause we can be quite sure, that after the recv we want to read at least the return-header
        # maybe make an argument, here
        ''' just get the answering head - we need at least this, to receive the body (else we won't know if the body is chunked and so on)
        also returns all already gathered pieces of the body '''
        buf = ''
        while True:
            buf += self.c.recv(4096)
            x = buf.find('\r\n\r\n')
            if x != -1:
                self.buf = buf[x+4:]
                break
        self.head = header(buf[:x+2]) # keep the \r\n at the end, so we can search easier

    def get(self):
        if not self.head:
            self.get_head()
        body = self.buf
        if self.head.get('Location'):
            self.redirection = self.head.get('Location')
            self.c = http(self.redirection)
            self.c.open()
            body = self.c.get()
        else:
            if self.head.get('Transfer-Encoding') == 'chunked':
                body = self.get_chunks(body)
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
                while length > downloaded:
                    x = self.c.recv(length - downloaded)
                    if not x:
                        break
                    downloaded += len(x)
                    body += x

        self.c.close()
        if GZIP and self.head.get('Content-Encoding') == 'gzip':
            compressedstream = StringIO.StringIO(body)
            gzipper   = gzip.GzipFile(fileobj = compressedstream)
            body = gzipper.read()
        return body

    def get_redirection(self):
        if self.redirection:
            return self.redirection
        return ''

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
    a = http('http://79.173.104.28/25b43cd3e3cb31644dcc43a51991fd4c672d0623bf713bc2f062b5be178f853c')
    a.header.append('User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062417 (Gentoo) Iceweasel/3.0.1')
    a.header.append('Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    a.header.append('Accept-Language: en-us,en;q=0.5')
    a.header.append('Accept-Charset: utf-8,ISO-8859-1;q=0.7,*;q=0.7')


    a.open()
    print a.head.plain()
