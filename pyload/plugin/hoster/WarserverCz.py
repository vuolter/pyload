# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class WarserverCz(DeadHoster):
    __name__    = "WarserverCz"
    __type__    = "hoster"
    __version__ = "0.13"

    __pattern__ = r'http://(?:www\.)?warserver\.cz/stahnout/\d+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Warserver.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
