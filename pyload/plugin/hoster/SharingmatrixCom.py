# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class SharingmatrixCom(DeadHoster):
    __name    = "SharingmatrixCom"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sharingmatrix\.com/file/\w+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Sharingmatrix.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de"),
                       ("paulking", "")]
