# -*- coding: utf-8 -*-

from pyload.plugin.account.ZeveraCom import ZeveraCom


class Multihosters_com(Zevera_com):
    __name    = "MultihostersCom"
    __type    = "account"
    __version = "0.03"

    __description = """Multihosters.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("tjeh", "tjeh@gmx.net")]


    HOSTER_DOMAIN = "multihosters.com"
