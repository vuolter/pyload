# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import with_statement

import cStringIO
import codecs
import httplib
import logging
import urllib

import pycurl

from pyload.plugin.Plugin import Abort, Fail

from pyload.misc import encode


bad_headers = range(400, 404) + range(405, 418) + range(500, 506)


class BadHeader(Exception):

    def __init__(self, code, content=""):
        Exception.__init__(self, "Bad server response: %s %s" % (code, httplib.responses[int(code)]))
        self.code = code
        self.content = content


class HTTPRequest(object):

    def __init__(self, cookies=None, options=None):
        self.c = pycurl.Curl()
        self.rep = cStringIO.StringIO()

        self.cj = cookies  #: cookiejar

        self.lastURL = None
        self.lastEffectiveURL = None
        self.abort = False
        self.code = 0  #: last http code

        self.header = ""

        self.headers = []  #: temporary request header

        self.init_handle()
        self.set_interface(options)

        self.c.setopt(pycurl.WRITEFUNCTION, self.write)
        self.c.setopt(pycurl.HEADERFUNCTION, self.writeHeader)

        self.log = logging.get_logger("log")


    def init_handle(self):
        """Sets common options to curl handle"""
        self.c.setopt(pycurl.FOLLOWLOCATION, 1)
        self.c.setopt(pycurl.MAXREDIRS, 10)
        self.c.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.c.setopt(pycurl.NOSIGNAL, 1)
        self.c.setopt(pycurl.NOPROGRESS, 1)
        if hasattr(pycurl, "AUTOREFERER"):
            self.c.setopt(pycurl.AUTOREFERER, 1)
        self.c.setopt(pycurl.SSL_VERIFYPEER, 0)
        self.c.setopt(pycurl.LOW_SPEED_TIME, 60)
        self.c.setopt(pycurl.LOW_SPEED_LIMIT, 5)
        if hasattr(pycurl, "USE_SSL"):
            self.c.setopt(pycurl.USE_SSL, pycurl.CURLUSESSL_TRY)

        # self.c.setopt(pycurl.VERBOSE, 1)

        self.c.setopt(pycurl.USERAGENT,
                      "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0")

        if pycurl.version_info()[7]:
            self.c.setopt(pycurl.ENCODING, "gzip, deflate")
        self.c.setopt(pycurl.HTTPHEADER, ["Accept: */*",
                                          "Accept-Language: en-US, en",
                                          "Accept-Charset: ISO-8859-1, utf-8;q=0.7,*;q=0.7",
                                          "Connection: keep-alive",
                                          "Keep-Alive: 300",
                                          "Expect:"])


    def set_interface(self, options):

        interface, proxy, ipv6 = options['interface'], options['proxies'], options['ipv6']

        if interface and interface.lower() != "none":
            self.c.setopt(pycurl.INTERFACE, str(interface))

        if proxy:
            if proxy['type'] == "socks4":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
            elif proxy['type'] == "socks5":
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            else:
                self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)

            self.c.setopt(pycurl.PROXY, str(proxy['ip']))
            self.c.setopt(pycurl.PROXYPORT, proxy['port'])

            if proxy['username']:
                self.c.setopt(pycurl.PROXYUSERPWD, str("%s:%s" % (proxy['username'], proxy['password'])))

        if ipv6:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
        else:
            self.c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)

        if "auth" in options:
            self.c.setopt(pycurl.USERPWD, str(options['auth']))

        if "timeout" in options:
            self.c.setopt(pycurl.LOW_SPEED_TIME, options['timeout'])


    def add_cookies(self):
        """Put cookies from curl handle to cj"""
        if self.cj:
            self.cj.add_cookies(self.c.getinfo(pycurl.INFO_COOKIELIST))


    def get_cookies(self):
        """Add cookies from cj to curl handle"""
        if self.cj:
            for c in self.cj.get_cookies():
                self.c.setopt(pycurl.COOKIELIST, c)
        return


    def clear_cookies(self):
        self.c.setopt(pycurl.COOKIELIST, "")


    def set_request_context(self, url, get, post, referer, cookies, multipart=False):
        """Sets everything needed for the request"""

        url = urllib.quote(encode(url).strip(), safe="%/:=&?~#+!$,;'@()*[]")  #@TODO: recheck

        if get:
            get = urllib.urlencode(get)
            url = "%s?%s" % (url, get)

        self.c.setopt(pycurl.URL, url)
        self.c.lastUrl = url

        if post:
            self.c.setopt(pycurl.POST, 1)
            if not multipart:
                if type(post) == unicode:
                    post = str(post)  #: unicode not allowed
                elif type(post) == str:
                    pass
                else:
                    post = urllib.urlencode(dict((encode(x), encode(y)) for x, y in dict(post).iteritems()))

                self.c.setopt(pycurl.POSTFIELDS, post)
            else:
                post = [(x, encode(y)) for x, y in post.iteritems()]
                self.c.setopt(pycurl.HTTPPOST, post)
        else:
            self.c.setopt(pycurl.POST, 0)

        if referer and self.lastURL:
            self.c.setopt(pycurl.REFERER, str(self.lastURL))

        if cookies:
            self.c.setopt(pycurl.COOKIEFILE, "")
            self.c.setopt(pycurl.COOKIEJAR, "")
            self.get_cookies()


    def load(self, url, get={}, post={}, referer=True, cookies=True, just_header=False, multipart=False, decode=False, follow_location=True, save_cookies=True):
        """Load and returns a given page"""

        self.set_request_context(url, get, post, referer, cookies, multipart)

        self.header = ""

        self.c.setopt(pycurl.HTTPHEADER, self.headers)

        if post:
            self.c.setopt(pycurl.POST, 1)
        else:
            self.c.setopt(pycurl.HTTPGET, 1)

        if not follow_location:
            self.c.setopt(pycurl.FOLLOWLOCATION, 0)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 1)

        self.c.perform()
        rep = self.header if just_header else self.get_response()

        if not follow_location:
            self.c.setopt(pycurl.FOLLOWLOCATION, 1)

        if just_header:
            self.c.setopt(pycurl.NOBODY, 0)

        self.c.setopt(pycurl.POSTFIELDS, "")
        self.lastEffectiveURL = self.c.getinfo(pycurl.EFFECTIVE_URL)
        self.code = self.verify_header()

        if save_cookies:
            self.add_cookies()

        if decode:
            rep = self.decode_response(rep)

        return rep


    def verify_header(self):
        """Raise an exceptions on bad headers"""
        code = int(self.c.getinfo(pycurl.RESPONSE_CODE))
        if code in bad_headers:
            # 404 will NOT raise an exception
            raise BadHeader(code, self.get_response())
        return code


    def check_header(self):
        """Check if header indicates failure"""
        return int(self.c.getinfo(pycurl.RESPONSE_CODE)) not in bad_headers


    def get_response(self):
        """Retrieve response from string io"""
        if self.rep is None:
            return ""
        else:
            value = self.rep.getvalue()
            self.rep.close()
            self.rep = cStringIO.StringIO()
            return value


    def decode_response(self, rep):
        """Decode with correct encoding, relies on header"""
        header = self.header.splitlines()
        encoding = "utf8"  #: default encoding

        for line in header:
            line = line.lower().replace(" ", "")
            if not line.startswith("content-type:") or \
                    ("text" not in line and "application" not in line):
                continue

            none, delemiter, charset = line.rpartition("charset=")
            if delemiter:
                charset = charset.split(";")
                if charset:
                    encoding = charset[0]

        try:
            # self.log.debug("Decoded %s" % encoding )
            if codecs.lookup(encoding).name == 'utf-8' and rep.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8-sig'

            decoder = codecs.getincrementaldecoder(encoding)("replace")
            rep = decoder.decode(rep, True)

            # TODO: html_unescape as default

        except LookupError:
            self.log.debug("No Decoder foung for %s" % encoding)

        except Exception:
            self.log.debug("Error when decoding string from %s." % encoding)

        return rep


    def write(self, buf):
        """Writes response"""
        if self.rep.tell() > 1000000 or self.abort:
            rep = self.get_response()

            if self.abort:
                raise Abort

            with open("response.dump", "wb") as f:
                f.write(rep)
            raise Fail("Loaded url exceeded size limit")
        else:
            self.rep.write(buf)


    def write_header(self, buf):
        """Writes header"""
        self.header += buf


    def put_header(self, name, value):
        self.headers.append("%s: %s" % (name, value))


    def clear_headers(self):
        self.headers = []


    def close(self):
        """Cleanup, unusable after this"""
        self.rep.close()
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "c"):
            self.c.close()
            del self.c
