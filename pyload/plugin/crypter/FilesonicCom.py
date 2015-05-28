# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class FilesonicCom(DeadCrypter):
    __name    = "FilesonicCom"
    __type    = "crypter"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?filesonic\.com/folder/\w+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Filesonic.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
