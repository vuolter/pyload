# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class MultiuploadCom(DeadCrypter):
    __name    = "MultiuploadCom"
    __type    = "crypter"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?multiupload\.(com|nl)/\w+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """MultiUpload.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
