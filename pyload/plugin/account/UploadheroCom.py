# -*- coding: utf-8 -*-

import re
import datetime
import time

from pyload.plugin.Account import Account


class Uploadhero_com(Account):
    __name    = "UploadheroCom"
    __type    = "account"
    __version = "0.21"

    __description = """Uploadhero.co account plugin"""
    __license     = "GPLv3"
    __authors     = [("mcmyst", "mcmyst@hotmail.fr")]


    def load_account_info(self, user, req):
        premium_pattern = re.compile('Il vous reste <span class="bleu">(\d+)</span> jours premium')

        data = self.get_account_data(user)
        html = req.load("http://uploadhero.co/my-account")

        if premium_pattern.search(html):
            end_date = datetime.date.today() + datetime.timedelta(days=int(premium_pattern.search(html).group(1)))
            end_date = time.mktime(future.timetuple())
            account_info = {"validuntil": end_date, "trafficleft": -1, "premium": True}
        else:
            account_info = {"validuntil": -1, "trafficleft": -1, "premium": False}

        return account_info


    def login(self, user, data, req):
        html = req.load("http://uploadhero.co/lib/connexion.php",
                        post={"pseudo_login": user, "password_login": data['password']},
                        decode=True)

        if "mot de passe invalide" in html:
            self.wrong_password()
