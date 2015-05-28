# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class NahrajCz(DeadHoster):
    __name    = "NahrajCz"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?nahraj\.cz/content/download/.+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Nahraj.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
