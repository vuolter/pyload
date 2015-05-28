# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class PrzeklejPl(DeadHoster):
    __name    = "PrzeklejPl"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?przeklej\.pl/plik/.+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Przeklej.pl hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
