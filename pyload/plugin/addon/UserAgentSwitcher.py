# -*- coding: utf-8 -*-

import pycurl

from pyload.plugin.Addon import Addon
from pyload.utils import encode


class UserAgentSwitcher(Hook):
    __name__    = "UserAgentSwitcher"
    __type__    = "hook"
    __version__ = "0.07"

    __config = [("activated", "bool", "Activated"                , True                                                                      ),
                ("useragent", "str" , "Custom user-agent string" , "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0")]

    __description__ = """Custom user-agent"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def downloadPreparing(self, pyfile):
        useragent = encode(self.getConfig('useragent'))  #@TODO: Remove `encode` in 0.4.10
        if useragent:
            self.logDebug("Use custom user-agent string: " + useragent)
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, useragent)
