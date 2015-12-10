# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class File_ape_com(Dead_hoster):
    __name    = "FileApeCom"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+'
    __config  = []

    __description = """FileApe.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("espes", "")]
