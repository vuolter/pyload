# -*- coding: utf-8 -*-
#
# Test links:
#   https://www.oboom.com/B7CYZIEB/10Mio.dat

import re

from pyload.utils import json_loads
from pyload.plugin.Hoster import Hoster
from pyload.plugin.captcha.ReCaptcha import ReCaptcha


class Oboom_com(Hoster):
    __name    = "OboomCom"
    __type    = "hoster"
    __version = "0.31"

    __pattern = r'https?://(?:www\.)?oboom\.com/(#(id=|/)?)?(?P<ID>\w{8})'

    __description = """oboom.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stanley", "stanley.foerster@gmail.com")]


    RECAPTCHA_KEY = "6LdqpO0SAAAAAJGHXo63HyalP7H4qlRs_vff0kJX"


    def setup(self):
        self.chunkLimit = 1
        self.multiDL = self.resumeDownload = self.premium


    def process(self, pyfile):
        self.pyfile.url.replace(".com/#id=", ".com/#")
        self.pyfile.url.replace(".com/#/", ".com/#")
        self.get_file_id(self.pyfile.url)
        self.get_session_token()
        self.get_file_info(self.sessionToken, self.fileId)
        self.pyfile.name = self.fileName
        self.pyfile.size = self.fileSize
        if not self.premium:
            self.solve_captcha()
        self.get_download_ticket()
        self.download("https://%s/1.0/dlh" % self.downloadDomain, get={"ticket": self.downloadTicket, "http_errors": 0})


    def load_url(self, url, get=None):
        if get is None:
            get = dict()
        return json_loads(self.load(url, get, decode=True))


    def get_file_id(self, url):
        self.fileId = re.match(OboomCom.__pattern, url).group('ID')


    def get_session_token(self):
        if self.premium:
            accountInfo = self.account.get_account_info(self.user, True)
            if "session" in accountInfo:
                self.sessionToken = accountInfo['session']
            else:
                self.fail(_("Could not retrieve premium session"))
        else:
            apiUrl = "https://www.oboom.com/1.0/guestsession"
            result = self.load_url(apiUrl)
            if result[0] == 200:
                self.sessionToken = result[1]
            else:
                self.fail(_("Could not retrieve token for guest session. Error code: %s") % result[0])


    def solve_captcha(self):
        recaptcha = ReCaptcha(self)

        for _i in xrange(5):
            response, challenge = recaptcha.challenge(self.RECAPTCHA_KEY)
            apiUrl = "https://www.oboom.com/1.0/download/ticket"
            params = {"recaptcha_challenge_field": challenge,
                      "recaptcha_response_field": response,
                      "download_id": self.fileId,
                      "token": self.sessionToken}
            result = self.load_url(apiUrl, params)

            if result[0] == 200:
                self.downloadToken = result[1]
                self.downloadAuth = result[2]
                self.correct_captcha()
                self.set_wait(30)
                self.wait()
                break

            elif result[0] == 400:
                if result[1] == "incorrect-captcha-sol":
                    self.invalid_captcha()
                elif result[1] == "captcha-timeout":
                    self.invalid_captcha()
                elif result[1] == "forbidden":
                    self.retry(5, 15 * 60, _("Service unavailable"))

            elif result[0] == 403:
                if result[1] == -1:  #: another download is running
                    self.set_wait(15 * 60)
                else:
                    self.set_wait(result[1], True)
                self.wait()
                self.retry(5)
        else:
            self.invalid_captcha()
            self.fail(_("Received invalid captcha 5 times"))


    def get_file_info(self, token, file_id):
        apiUrl = "https://api.oboom.com/1.0/info"
        params = {"token": token, "items": fileId, "http_errors": 0}

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            item = result[1][0]
            if item['state'] == "online":
                self.fileSize = item['size']
                self.fileName = item['name']
            else:
                self.offline()
        else:
            self.fail(_("Could not retrieve file info. Error code %s: %s") % (result[0], result[1]))


    def get_download_ticket(self):
        apiUrl = "https://api.oboom.com/1/dl"
        params = {"item": self.fileId, "http_errors": 0}
        if self.premium:
            params['token'] = self.sessionToken
        else:
            params['token'] = self.downloadToken
            params['auth'] = self.downloadAuth

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            self.downloadDomain = result[1]
            self.downloadTicket = result[2]
        elif result[0] == 421:
            self.retry(wait_time=result[2] + 60, reason=_("Connection limit exceeded"))
        else:
            self.fail(_("Could not retrieve download ticket. Error code: %s") % result[0])
