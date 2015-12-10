# -*- coding: utf-8 -*-

import pycurl
import re
import urllib
import urlparse

from pyload.plugin.Hoster import Hoster


class Ftp(Hoster):
    __name    = "Ftp"
    __type    = "hoster"
    __version = "0.51"

    __pattern = r'(?:ftps?|sftp)://([\w.-]+(:[\w.-]+)?@)?[\w.-]+(:\d+)?/.+'

    __description = """Download from ftp directory"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.com"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True
    def process(self, pyfile):
        parsed_url = urlparse.urlparse(pyfile.url)
        netloc = parsed_url.netloc

        pyfile.name = parsed_url.path.rpartition('/')[2]
        try:
            pyfile.name = urllib.unquote(str(pyfile.name)).decode('utf8')
        except Exception:
            pass

        if not "@" in netloc:
            servers = [x['login'] for x in self.account.get_all_accounts()] if self.account else []

            if netloc in servers:
                self.log_debug("Logging on to %s" % netloc)
                self.req.add_auth(self.account.get_account_info(netloc)['password'])
            else:
                pwd = self.get_password()
                if ':' in pwd:
                    self.req.add_auth(pwd)

        self.req.http.c.setopt(pycurl.NOBODY, 1)

        try:
            res = self.load(pyfile.url)
        except pycurl.error, e:
            self.fail(_("Error %d: %s") % e.args)

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.log_debug(self.req.http.header)

        m = re.search(r"Content-Length:\s*(\d+)", res)
        if m:
            pyfile.size = int(m.group(1))
            self.download(pyfile.url)
        else:
            # Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):
                pyfile.url = pyfile.url.rstrip('/')
                pkgname = "/".join(pyfile.package().name, urlparse.urlparse(pyfile.url).path.rpartition('/')[2])
                pyfile.url += '/'
                self.req.http.c.setopt(48, 1)  #: CURLOPT_DIRLISTONLY
                res = self.load(pyfile.url, decode=False)
                links = [pyfile.url + urllib.quote(x) for x in res.splitlines()]
                self.log_debug("LINKS", links)
                self.pyload.api.add_package(pkgname, links)
            else:
                self.fail(_("Unexpected server response"))
