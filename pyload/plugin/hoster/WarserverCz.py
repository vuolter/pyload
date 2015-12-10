# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Warserver_cz(Dead_hoster):
    __name    = "WarserverCz"
    __type    = "hoster"
    __version = "0.13"

    __pattern = r'http://(?:www\.)?warserver\.cz/stahnout/\d+'
    __config  = []

    __description = """Warserver.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]
