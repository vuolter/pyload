# -*- coding: utf-8 -*-

import logging

from pyload.network.HTTPRequest import HTTPRequest
from pyload.network.HTTPDownload import HTTPDownload


class Browser(object):
    __slots__ = ("log", "options", "bucket", "cj", "_size", "http", "dl")


    def __init__(self, bucket=None, options={}):
        self.log = logging.get_logger("log")

        self.options = options  #: holds pycurl options
        self.bucket = bucket

        self.cj = None  #: needs to be setted later
        self._size = 0

        self.renew_HTTP_request()
        self.dl = None


    def renew_HTTP_request(self):
        if hasattr(self, "http"):
            self.http.close()
        self.http = HTTPRequest(self.cj, self.options)


    def set_lastURL(self, val):
        self.http.lastURL = val

    # tunnel some attributes from HTTP Request to Browser
    lastEffectiveURL = property(lambda self: self.http.lastEffectiveURL)
    lastURL = property(lambda self: self.http.lastURL, setLastURL)
    code = property(lambda self: self.http.code)
    cookieJar = property(lambda self: self.cj)


    def set_cookie_jar(self, cj):
        self.cj = cj
        self.http.cj = cj


    @property
    def speed(self):
        if self.dl:
            return self.dl.speed
        return 0


    @property
    def size(self):
        if self._size:
            return self._size
        if self.dl:
            return self.dl.size
        return 0


    @property
    def arrived(self):
        return self.dl.arrived if self.dl else 0


    @property
    def percent(self):
        return (self.arrived * 100) / self.size if self.size else 0


    def clear_cookies(self):
        if self.cj:
            self.cj.clear()
        self.http.clear_cookies()


    def clear_referer(self):
        self.http.lastURL = None


    def abort_downloads(self):
        self.http.abort = True
        if self.dl:
            self._size = self.dl.size
            self.dl.abort = True


    def http_download(self, url, filename, get={}, post={}, ref=True, cookies=True, chunks=1, resume=False,
                     progressNotify=None, disposition=False):
        """This can also download ftp"""
        self._size = 0
        self.dl = HTTPDownload(url, filename, get, post, self.lastEffectiveURL if ref else None,
                               self.cj if cookies else None, self.bucket, self.options, progressNotify, disposition)
        name = self.dl.download(chunks, resume)
        self._size = self.dl.size

        self.dl = None

        return name


    def load(self, *args, **kwargs):
        """Retrieves page"""
        return self.http.load(*args, **kwargs)


    def put_header(self, name, value):
        """Add a header to the request"""
        self.http.put_header(name, value)


    def add_auth(self, pwd):
        """
        Adds user and pw for http auth

        :param pwd: string, user:password
        """
        self.options['auth'] = pwd
        self.renew_HTTP_request()  #: we need a new request


    def remove_auth(self):
        if "auth" in self.options:
            del self.options['auth']
        self.renew_HTTP_request()


    def set_option(self, name, value):
        """Adds an option to the request, see HTTPRequest for existing ones"""
        self.options[name] = value


    def delete_option(self, name):
        if name in self.options:
            del self.options[name]


    def clear_headers(self):
        self.http.clear_headers()


    def close(self):
        """Cleanup"""
        if hasattr(self, "http"):
            self.http.close()
            del self.http
        if hasattr(self, "dl"):
            del self.dl
        if hasattr(self, "cj"):
            del self.cj
