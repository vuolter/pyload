# -*- coding: utf-8 -*-

from pyload.plugin.Hoster import Hoster as _Hoster


class DeadHoster(_Hoster):
    __name    = "DeadHoster"
    __type    = "hoster"
    __version = "0.15"

    __pattern = r'^unmatchable$'

    __description = """Hoster is no longer available"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def apiInfo(cls, *args, **kwargs):
        api = super(DeadHoster, cls).apiInfo(*args, **kwargs)
        api['status'] = 1
        return api


    def setup(self):
        self.pyfile.error = "Hoster is no longer available"
        self.offline()  #@TODO: self.offline("Hoster is no longer available")
