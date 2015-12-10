# -*- coding: utf-8 -*-

from __future__ import with_statement

import StringIO
import pycurl
import time
import urllib

try:
    from PIL import Image
except ImportError:
    import Image

from pyload.network.RequestFactory import getURL, getRequest
from pyload.plugin.Hook import Hook, threaded


class Captcha_brotherhood_exception(Exception):

    def __init__(self, err):
        self.err = err


    def get_code(self):
        return self.err


    def __str__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err


    def __repr__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err


class Captcha_brotherhood(Hook):
    __name    = "CaptchaBrotherhood"
    __type    = "hook"
    __version = "0.08"

    __config = [("username", "str", "Username", ""),
                ("force", "bool", "Force CT even if client is connected", False),
                ("passkey", "password", "Password", "")]

    __description = """Send captchas to CaptchaBrotherhood.com"""
    __license     = "GPLv3"
    __authors     = [("RaNaN"   , "RaNaN@pyload.org"),
                     ("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://www.captchabrotherhood.com/"


    def activate(self):
        if self.get_config('ssl'):
            self.API_URL = self.API_URL.replace("http://", "https://")


    def get_credits(self):
        res = getURL(self.API_URL + "askCredits.aspx",
                     get={"username": self.get_config('username'), "password": self.get_config('passkey')})
        if not res.startswith("OK"):
            raise CaptchaBrotherhoodException(res)
        else:
            credits = int(res[3:])
            self.log_info(_("%d credits left") % credits)
            self.info['credits'] = credits
            return credits


    def submit(self, captcha, captcha_type="file", match=None):
        try:
            img = Image.open(captcha)
            output = StringIO.StringIO()
            self.log_debug("CAPTCHA IMAGE", img, img.format, img.mode)
            if img.format in ("GIF", "JPEG"):
                img.save(output, img.format)
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output, "JPEG")
            data = output.getvalue()
            output.close()
        except Exception, e:
            raise CaptchaBrotherhoodException("Reading or converting captcha image failed: %s" % e)

        req = getRequest()

        url = "%ssendNewCaptcha.aspx?%s" % (self.API_URL,
                                            urllib.urlencode({'username'     : self.get_config('username'),
                                                              'password'     : self.get_config('passkey'),
                                                              'captchaSource': "pyLoad",
                                                              'timeout'      : "80"}))

        req.c.setopt(pycurl.URL, url)
        req.c.setopt(pycurl.POST, 1)
        req.c.setopt(pycurl.POSTFIELDS, data)
        req.c.setopt(pycurl.HTTPHEADER, ["Content-Type: text/html"])

        try:
            req.c.perform()
            res = req.getResponse()
        except Exception, e:
            raise CaptchaBrotherhoodException("Submit captcha image failed")

        req.close()

        if not res.startswith("OK"):
            raise CaptchaBrotherhoodException(res[1])

        ticket = res[3:]

        for _i in xrange(15):
            time.sleep(5)
            res = self.api_response("askCaptchaResult", ticket)
            if res.startswith("OK-answered"):
                return ticket, res[12:]

        raise CaptchaBrotherhoodException("No solution received in time")


    def api_response(self, api, ticket):
        res = getURL("%s%s.aspx" % (self.API_URL, api),
                     get={"username": self.get_config('username'),
                          "password": self.get_config('passkey'),
                          "captchaID": ticket})
        if not res.startswith("OK"):
            raise CaptchaBrotherhoodException("Unknown response: %s" % res)

        return res


    def captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.get_config('username') or not self.get_config('passkey'):
            return False

        if self.pyload.is_client_connected() and not self.get_config('force'):
            return False

        if self.get_credits() > 10:
            task.handler.append(self)
            task.data['service'] = self.get_class_name()
            task.setWaiting(100)
            self._process_captcha(task)
        else:
            self.log_info(_("Your CaptchaBrotherhood Account has not enough credits"))


    def captcha_invalid(self, task):
        if task.data['service'] == self.get_class_name() and "ticket" in task.data:
            res = self.api_response("complainCaptcha", task.data['ticket'])


    @threaded
    def _process_captcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaBrotherhoodException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
