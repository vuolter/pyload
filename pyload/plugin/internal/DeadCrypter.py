# -*- coding: utf-8 -*-

from pyload.plugin.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name    = "DeadCrypter"
    __type    = "crypter"
    __version = "0.05"

    __pattern = r'^unmatchable$'

    __description = """Crypter is no longer available"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    @classmethod
    def apiInfo(cls, *args, **kwargs):
        api = super(DeadCrypter, cls).apiInfo(*args, **kwargs)
        api['status'] = 1
        return api


    def setup(self):
        self.pyfile.error = "Crypter is no longer available"
        self.offline()  #@TODO: self.offline("Crypter is no longer available")
