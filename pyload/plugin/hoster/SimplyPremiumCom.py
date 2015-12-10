# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.plugin.internal.SimpleHoster import secondsToMidnight


class Simply_premium_com(Multi_hoster):
    __name    = "SimplyPremiumCom"
    __type    = "hoster"
    __version = "0.08"

    __pattern = r'https?://.+simply-premium\.com'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Simply-Premium.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("EvolutionClip", "evolutionclip@live.de")]


    def setup(self):
        self.chunkLimit = 16


    def check_errors(self):
        if '<valid>0</valid>' in self.html or (
                "You are not allowed to download from this host" in self.html and self.premium):
            self.account.relogin(self.user)
            self.retry()

        elif "NOTFOUND" in self.html:
            self.offline()

        elif "downloadlimit" in self.html:
            self.log_warning(_("Reached maximum connctions"))
            self.retry(5, 60, _("Reached maximum connctions"))

        elif "trafficlimit" in self.html:
            self.log_warning(_("Reached daily limit for this host"))
            self.retry(wait_time=seconds_to_midnight(gmt=2), reason="Daily limit for this host reached")

        elif "hostererror" in self.html:
            self.log_warning(_("Hoster temporarily unavailable, waiting 1 minute and retry"))
            self.retry(5, 60, _("Hoster is temporarily unavailable"))


    def handle_premium(self, pyfile):
        for _i in xrange(5):
            self.html = self.load("http://www.simply-premium.com/premium.php", get={'info': "", 'link': self.pyfile.url})

            if self.html:
                self.log_debug("JSON data: " + self.html)
                break
        else:
            self.log_info(_("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, _("Unable to get API data"))

        self.check_errors()

        try:
            self.pyfile.name = re.search(r'<name>([^<]+)</name>', self.html).group(1)

        except AttributeError:
            self.pyfile.name = ""

        try:
            self.pyfile.size = re.search(r'<size>(\d+)</size>', self.html).group(1)

        except AttributeError:
            self.pyfile.size = 0

        try:
            self.link = re.search(r'<download>([^<]+)</download>', self.html).group(1)

        except AttributeError:
            self.link = 'http://www.simply-premium.com/premium.php?link=' + self.pyfile.url
