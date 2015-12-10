# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import parse_size


class Over_load_me(Multi_hoster):
    __name    = "OverLoadMe"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'https?://.*overload\.me/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Over-Load.me multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("marley", "marley@over-load.me")]


    def setup(self):
        self.chunkLimit = 5


    def handle_premium(self, pyfile):
        https = "https" if self.get_config('ssl') else "http"
        data  = self.account.get_account_data(self.user)
        page  = self.load(https + "://api.over-load.me/getdownload.php",
                          get={'auth': data['password'],
                               'link': pyfile.url})

        data = json_loads(page)

        self.log_debug(data)

        if data['error'] == 1:
            self.log_warning(data['msg'])
            self.temp_offline()
        else:
            if pyfile.name and pyfile.name.endswith('.tmp') and data['filename']:
                pyfile.name = data['filename']
                pyfile.size = parse_size(data['filesize'])

            http_repl = ["http://", "https://"]
            self.link = data['downloadlink'].replace(*http_repl if self.get_config('ssl') else http_repl[::-1])
