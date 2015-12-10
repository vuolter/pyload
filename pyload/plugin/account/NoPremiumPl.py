# -*- coding: utf-8 -*-

import datetime
import hashlib
import time

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class No_premium_pl(Account):
    __name = "NoPremiumPl"
    __version = "0.01"
    __type = "account"
    __description = "NoPremium.pl account plugin"
    __license = "GPLv3"
    __authors = [("goddie", "dev@nopremium.pl")]

    _api_url = "http://crypt.nopremium.pl"

    _api_query = {
        "site": "nopremium",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1"
    }

    _req = None
    _usr = None
    _pwd = None


    def load_account_info(self, name, req):
        self._req = req
        try:
            result = json_loads(self.run_auth_query())
        except Exception:
            #@TODO: return or let it be thrown?
            return

        premium = False
        valid_untill = -1

        if "expire" in result.keys() and result['expire']:
            premium = True
            valid_untill = time.mktime(datetime.datetime.fromtimestamp(int(result['expire'])).timetuple())
        traffic_left = result['balance'] * 2 ** 20

        return ({
                    "validuntil": valid_untill,
                    "trafficleft": traffic_left,
                    "premium": premium
                })


    def login(self, user, data, req):
        self._usr = user
        self._pwd = hashlib.sha1(hashlib.md5(data['password']).hexdigest()).hexdigest()
        self._req = req

        try:
            response = json_loads(self.run_auth_query())
        except Exception:
            self.wrong_password()

        if "errno" in response.keys():
            self.wrong_password()
        data['usr'] = self._usr
        data['pwd'] = self._pwd


    def create_auth_query(self):
        query = self._api_query
        query['username'] = self._usr
        query['password'] = self._pwd

        return query


    def run_auth_query(self):
        data = self._req.load(self._api_url, post=self.create_auth_query())

        return data
