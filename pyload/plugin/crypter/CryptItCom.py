# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class CryptItCom(DeadCrypter):
    __name    = "CryptItCom"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?crypt-it\.com/(s|e|d|c)/\w+'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """Crypt-it.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de")]
