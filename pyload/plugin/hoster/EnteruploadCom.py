# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Enterupload_com(Dead_hoster):
    __name    = "EnteruploadCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?enterupload\.com/\w+'
    __config  = []

    __description = """EnterUpload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
