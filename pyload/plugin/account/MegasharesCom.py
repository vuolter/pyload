# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class Megashares_com(Account):
    __name    = "MegasharesCom"
    __type    = "account"
    __version = "0.03"

    __description = """Megashares.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    VALID_UNTIL_PATTERN = r'<p class="premium_info_box">Period Ends: (\w{3} \d{1,2}, \d{4})</p>'


    def load_account_info(self, user, req):
        # self.relogin(user)
        html = req.load("http://d01.megashares.com/myms.php", decode=True)

        premium = '>Premium Upgrade<' not in html

        validuntil = trafficleft = -1
        try:
            timestr = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
            self.log_debug(timestr)
            validuntil = time.mktime(time.strptime(timestr, "%b %d, %Y"))
        except Exception, e:
            self.log_error(e)

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}


    def login(self, user, data, req):
        html = req.load('http://d01.megashares.com/myms_login.php',
                        post={"httpref"       : "",
                              "myms_login"    : "Login",
                              "mymslogin_name": user,
                              "mymspassword"  : data['password']},
                        decode=True)

        if not '<span class="b ml">%s</span>' % user in html:
            self.wrong_password()
