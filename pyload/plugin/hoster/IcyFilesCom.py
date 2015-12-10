# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Icy_files_com(Dead_hoster):
    __name    = "IcyFilesCom"
    __type    = "hoster"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?icyfiles\.com/(.+)'
    __config  = []

    __description = """IcyFiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]
