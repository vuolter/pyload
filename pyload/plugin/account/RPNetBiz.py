# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class RPNet_biz(Account):
    __name    = "RPNetBiz"
    __type    = "account"
    __version = "0.12"

    __description = """RPNet.biz account plugin"""
    __license     = "GPLv3"
    __authors     = [("Dman", "dmanugm@gmail.com")]


    def load_account_info(self, user, req):
        # Get account information from rpnet.biz
        res = self.get_account_status(user, req)
        try:
            if res['accountInfo']['isPremium']:
                # Parse account info. Change the trafficleft later to support per host info.
                account_info = {"validuntil": float(res['accountInfo']['premiumExpiry']),
                                "trafficleft": -1, "premium": True}
            else:
                account_info = {"validuntil": None, "trafficleft": None, "premium": False}

        except KeyError:
            # handle wrong password exception
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}

        return account_info


    def login(self, user, data, req):
        # Get account information from rpnet.biz
        res = self.get_account_status(user, req)

        # If we have an error in the res, we have wrong login information
        if 'error' in res:
            self.wrong_password()


    def get_account_status(self, user, req):
        # Using the rpnet API, check if valid premium account
        res = req.load("https://premium.rpnet.biz/client_api.php",
                            get={"username": user, "password": self.get_account_data(user)['password'],
                                 "action": "showAccountInformation"})
        self.log_debug("JSON data: %s" % res)

        return json_loads(res)
