# -*- coding: utf-8 -*-

import time

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import parse_size


class Realdebrid_com(Multi_hoster):
    __name    = "RealdebridCom"
    __type    = "hoster"
    __version = "0.67"

    __pattern = r'https?://((?:www\.|s\d+\.)?real-debrid\.com/dl/|[\w^_]\.rdb\.so/d/)[\w^_]+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Real-Debrid.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def setup(self):
        self.chunkLimit = 3


    def handle_premium(self, pyfile):
        data = json_loads(self.load("https://real-debrid.com/ajax/unrestrict.php",
                                    get={'lang'    : "en",
                                         'link'    : pyfile.url,
                                         'password': self.get_password(),
                                         'time'    : int(time.time() * 1000)}))

        self.log_debug("Returned Data: %s" % data)

        if data['error'] != 0:
            if data['message'] == "Your file is unavailable on the hoster.":
                self.offline()
            else:
                self.log_warning(data['message'])
                self.temp_offline()
        else:
            if pyfile.name and pyfile.name.endswith('.tmp') and data['file_name']:
                pyfile.name = data['file_name']
            pyfile.size = parse_size(data['file_size'])
            self.link = data['generated_links'][0][-1]

        if self.get_config('ssl'):
            self.link = self.link.replace("http://", "https://")
        else:
            self.link = self.link.replace("https://", "http://")
