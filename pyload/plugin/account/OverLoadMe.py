# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class Over_load_me(Account):
    __name    = "OverLoadMe"
    __type    = "account"
    __version = "0.04"

    __description = """Over-Load.me account plugin"""
    __license     = "GPLv3"
    __authors     = [("marley", "marley@over-load.me")]


    def load_account_info(self, user, req):
        https = "https" if self.get_config('ssl') else "http"
        data  = self.get_account_data(user)
        html  = req.load(https + "://api.over-load.me/account.php",
                         get={'user': user,
                              'auth': data['password']}).strip()

        data = json_loads(html)
        self.log_debug(data)

        # Check for premium
        if data['membership'] == "Free":
            return {'premium': False, 'validuntil': None, 'trafficleft': None}
        else:
            return {'premium': True, 'validuntil': data['expirationunix'], 'trafficleft': -1}


    def login(self, user, data, req):
        https    = "https" if self.get_config('ssl') else "http"
        jsondata = req.load(https + "://api.over-load.me/account.php",
                            get={'user': user,
                                 'auth': data['password']}).strip()

        data = json_loads(jsondata)

        if data['err'] == 1:
            self.wrong_password()
