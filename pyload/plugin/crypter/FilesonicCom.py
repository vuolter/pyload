# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class Filesonic_com(Dead_crypter):
    __name    = "FilesonicCom"
    __type    = "crypter"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?filesonic\.com/folder/\w+'
    __config  = []

    __description = """Filesonic.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
