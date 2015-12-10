# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class Ego_files_com(Dead_hoster):
    __name    = "EgoFilesCom"
    __type    = "hoster"
    __version = "0.16"

    __pattern = r'https?://(?:www\.)?egofiles\.com/\w+'
    __config  = []

    __description = """Egofiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
