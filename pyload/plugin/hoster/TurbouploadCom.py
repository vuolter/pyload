# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Turboupload_com(Dead_hoster):
    __name    = "TurbouploadCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?turboupload\.com/(\w+)'
    __config  = []

    __description = """Turboupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
