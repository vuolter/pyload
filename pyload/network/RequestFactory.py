# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

import threading

from pyload.network.Browser import Browser
from pyload.network.Bucket import Bucket
from pyload.network.CookieJar import CookieJar
from pyload.network.HTTPRequest import HTTPRequest
from pyload.network.XDCCRequest import XDCCRequest


class Request_factory(object):

    def __init__(self, core):
        self.lock = threading.Lock()
        self.pyload = core
        self.bucket = Bucket()
        self.update_bucket()
        self.cookiejars = {}


    def iface(self):
        return self.pyload.config.get("download", "interface")


    def get_request(self, plugin_name, account=None, type="HTTP"):
        self.lock.acquire()

        if type == "XDCC":
            return XDCCRequest(proxies=self.get_proxies())

        req = Browser(self.bucket, self.get_options())

        if account:
            cj = self.get_cookie_jar(pluginName, account)
            req.setCookieJar(cj)
        else:
            req.setCookieJar(CookieJar(pluginName))

        self.lock.release()
        return req


    def get_HTTP_request(self, **kwargs):
        """Returns a http request, dont forget to close it !"""
        options = self.get_options()
        options.update(kwargs)  #: submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)


    def getURL(self, *args, **kwargs):
        """See HTTPRequest for argument list"""
        cj = None

        if 'cookies' in kwargs:
            if isinstance(kwargs['cookies'], CookieJar):
                cj = kwargs['cookies']
            elif isinstance(kwargs['cookies'], list):
                cj = CookieJar(None)
                for cookie in kwargs['cookies']:
                    if isinstance(cookie, tuple) and len(cookie) == 3:
                        cj.setCookie(*cookie)

        h = HTTPRequest(cj, self.get_options())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep


    def get_cookie_jar(self, plugin_name, account=None):
        if (pluginName, account) in self.cookiejars:
            return self.cookiejars[(pluginName, account)]

        cj = CookieJar(pluginName, account)
        self.cookiejars[(pluginName, account)] = cj
        return cj


    def get_proxies(self):
        """Returns a proxy list for the request classes"""
        if not self.pyload.config.get("proxy", "activated"):
            return {}
        else:
            type = "http"
            setting = self.pyload.config.get("proxy", "type").lower()
            if setting == "socks4":
                type = "socks4"
            elif setting == "socks5":
                type = "socks5"

            username = None
            if self.pyload.config.get("proxy", "username") and self.pyload.config.get("proxy", "username").lower() != "none":
                username = self.pyload.config.get("proxy", "username")

            pw = None
            if self.pyload.config.get("proxy", "password") and self.pyload.config.get("proxy", "password").lower() != "none":
                pw = self.pyload.config.get("proxy", "password")

            return {
                "type": type,
                "ip": self.pyload.config.get("proxy", "ip"),
                "port": self.pyload.config.get("proxy", "port"),
                "username": username,
                "password": pw,
            }


    def get_options(self):
        """Returns options needed for pycurl"""
        return {"interface": self.iface(),
                "proxies": self.get_proxies(),
                "ipv6": self.pyload.config.get("download", "ipv6")}


    def update_bucket(self):
        """Set values in the bucket according to settings"""
        if not self.pyload.config.get("download", "limit_speed"):
            self.bucket.set_rate(-1)
        else:
            self.bucket.set_rate(self.pyload.config.get("download", "max_speed") * 1024)


# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def get_request(*args, **kwargs):
    return pyreq.getHTTPRequest()
