# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Przeklej_pl(Dead_hoster):
    __name    = "PrzeklejPl"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?przeklej\.pl/plik/.+'
    __config  = []

    __description = """Przeklej.pl hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
