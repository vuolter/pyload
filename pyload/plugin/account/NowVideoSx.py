# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class Now_video_sx(Account):
    __name    = "NowVideoSx"
    __type    = "account"
    __version = "0.03"

    __description = """NowVideo.at account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    VALID_UNTIL_PATTERN = r'>Your premium membership expires on: (.+?)<'


    def load_account_info(self, user, req):
        validuntil  = None
        trafficleft = -1
        premium     = None

        html = req.load("http://www.nowvideo.sx/premium.php")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%Y-%b-%d"))

            except Exception, e:
                self.log_error(e)

            else:
                if validuntil > time.mktime(time.gmtime()):
                    premium = True
                else:
                    premium = False
                    validuntil = -1

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        html = req.load("http://www.nowvideo.sx/login.php",
                        post={'user': user, 'pass': data['password']},
                        decode=True)

        if re.search(r'>Log In<', html):
            self.wrong_password()
