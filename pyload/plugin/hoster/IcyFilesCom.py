# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class IcyFilesCom(DeadHoster):
    __name    = "IcyFilesCom"
    __type    = "hoster"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?icyfiles\.com/(.+)'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """IcyFiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]
