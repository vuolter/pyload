# -*- coding: utf-8 -*-

import random
import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class GigapetaCom(SimpleHoster):
    __name__    = "GigapetaCom"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?gigapeta\.com/dl/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """GigaPeta.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<img src=".*" alt="file" />-->\s*(?P<N>.*?)\s*</td>'
    SIZE_PATTERN    = r'<th>\s*Size\s*</th>\s*<td>\s*(?P<S>.*?)\s*</td>'
    OFFLINE_PATTERN = r'<div id="page_error">'

    DOWNLOAD_PATTERN = r'"All threads for IP'

    COOKIES = [("gigapeta.com", "lang", "us")]


    def handle_free(self, pyfile):
        captcha_key = str(random.randint(1, 100000000))
        captcha_url = "http://gigapeta.com/img/captcha.gif?x=%s" % captcha_key

        for _i in xrange(5):
            self.checkErrors()

            captcha = self.decryptCaptcha(captcha_url)
            self.html = self.load(pyfile.url,
                                  post={'captcha_key': captcha_key,
                                        'captcha'    : captcha,
                                        'download'   : "Download"},
                                  follow_location=False)

            m = re.search(r'Location\s*:\s*(.+)', self.req.http.header, re.I)
            if m:
                self.link = m.group(1)
                break
            elif "Entered figures don&#96;t coincide with the picture" in self.html:
                self.invalidCaptcha()
        else:
            self.fail(_("No valid captcha code entered"))


