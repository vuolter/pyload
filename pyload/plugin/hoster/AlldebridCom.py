# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import parse_size


class Alldebrid_com(Multi_hoster):
    __name    = "AlldebridCom"
    __type    = "hoster"
    __version = "0.46"

    __pattern = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Alldebrid.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Andy Voigt", "spamsales@online.de")]


    def setup(self):
        self.chunkLimit = 16


    def handle_premium(self, pyfile):
        password = self.get_password()

        data = json_loads(self.load("http://www.alldebrid.com/service.php",
                                     get={'link': pyfile.url, 'json': "true", 'pw': password}))

        self.log_debug("Json data", data)

        if data['error']:
            if data['error'] == "This link isn't available on the hoster website.":
                self.offline()
            else:
                self.log_warning(data['error'])
                self.temp_offline()
        else:
            if pyfile.name and not pyfile.name.endswith('.tmp'):
                pyfile.name = data['filename']
            pyfile.size = parse_size(data['filesize'])
            self.link = data['link']

        if self.get_config('ssl'):
            self.link = self.link.replace("http://", "https://")
        else:
            self.link = self.link.replace("https://", "http://")
