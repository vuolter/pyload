# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Kickload_com(Dead_hoster):
    __name    = "KickloadCom"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?kickload\.com/get/.+'
    __config  = []

    __description = """Kickload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]
