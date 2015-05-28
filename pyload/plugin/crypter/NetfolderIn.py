# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class NetfolderIn(DeadCrypter):
    __name    = "NetfolderIn"
    __type    = "crypter"
    __version = "0.73"

    __pattern = r'http://(?:www\.)?netfolder\.(in|me)/(folder\.php\?folder_id=)?(?P<ID>\w+)(?(1)|/\w+)'
    __config  = []  #@TODO: Remove in 0.4.10

    __description = """NetFolder.in decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("fragonib", "fragonib[AT]yahoo[DOT]es")]

