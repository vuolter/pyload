# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class CryptItCom(DeadCrypter):
    __name__    = "CryptItCom"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?crypt-it\.com/(s|e|d|c)/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Crypt-it.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de")]
