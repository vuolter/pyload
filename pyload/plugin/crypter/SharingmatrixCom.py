# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class SharingmatrixCom(DeadCrypter):
    __name    = "SharingmatrixCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sharingmatrix\.com/folder/\w+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Sharingmatrix.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
