# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class Free_way_me(Account):
    __name    = "FreeWayMe"
    __type    = "account"
    __version = "0.13"

    __description = """FreeWayMe account plugin"""
    __license     = "GPLv3"
    __authors     = [("Nicolas Giese", "james@free-way.me")]


    def load_account_info(self, user, req):
        status = self.get_account_status(user, req)

        self.log_debug(status)

        account_info = {"validuntil": -1, "premium": False}
        if status['premium'] == "Free":
            account_info['trafficleft'] = self.parse_traffic(status['guthaben'] + "MB")
        elif status['premium'] == "Spender":
            account_info['trafficleft'] = -1
        elif status['premium'] == "Flatrate":
            account_info = {"validuntil": float(status['Flatrate']),
                            "trafficleft": -1,
                            "premium": True}

        return account_info


    def login(self, user, data, req):
        status = self.get_account_status(user, req)

        # Check if user and password are valid
        if not status:
            self.wrong_password()


    def get_account_status(self, user, req):
        answer = req.load("https://www.free-way.me/ajax/jd.php",
                          get={"id": 4, "user": user, "pass": self.get_account_data(user)['password']})

        self.log_debug("Login: %s" % answer)

        if answer == "Invalid login":
            self.wrong_password()

        return json_loads(answer)
