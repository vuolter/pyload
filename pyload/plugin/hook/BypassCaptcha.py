# -*- coding: utf-8 -*-

import pycurl

from pyload.network.HTTPRequest import BadHeader
from pyload.network.RequestFactory import getURL, getRequest
from pyload.plugin.Hook import Hook, threaded


class Bypass_captcha_exception(Exception):

    def __init__(self, err):
        self.err = err


    def get_code(self):
        return self.err


    def __str__(self):
        return "<BypassCaptchaException %s>" % self.err


    def __repr__(self):
        return "<BypassCaptchaException %s>" % self.err


class Bypass_captcha(Hook):
    __name    = "BypassCaptcha"
    __type    = "hook"
    __version = "0.06"

    __config = [("force", "bool", "Force BC even if client is connected", False),
                ("passkey", "password", "Passkey", "")]

    __description = """Send captchas to BypassCaptcha.com"""
    __license     = "GPLv3"
    __authors     = [("RaNaN"     , "RaNaN@pyload.org"),
                     ("Godofdream", "soilfcition@gmail.com"),
                     ("zoidberg"  , "zoidberg@mujmail.cz")]


    PYLOAD_KEY = "4f771155b640970d5607f919a615bdefc67e7d32"

    SUBMIT_URL = "http://bypasscaptcha.com/upload.php"
    RESPOND_URL = "http://bypasscaptcha.com/check_value.php"
    GETCREDITS_URL = "http://bypasscaptcha.com/ex_left.php"


    def get_credits(self):
        res = getURL(self.GETCREDITS_URL, post={"key": self.get_config('passkey')})

        data = dict(x.split(' ', 1) for x in res.splitlines())
        return int(data['Left'])


    def submit(self, captcha, captcha_type="file", match=None):
        req = getRequest()

        # raise timeout threshold
        req.c.setopt(pycurl.LOW_SPEED_TIME, 80)

        try:
            res = req.load(self.SUBMIT_URL,
                           post={'vendor_key': self.PYLOAD_KEY,
                                 'key': self.get_config('passkey'),
                                 'gen_task_id': "1",
                                 'file': (pycurl.FORM_FILE, captcha)},
                           multipart=True)
        finally:
            req.close()

        data = dict(x.split(' ', 1) for x in res.splitlines())
        if not data or "Value" not in data:
            raise BypassCaptchaException(res)

        result = data['Value']
        ticket = data['TaskId']
        self.log_debug("Result %s : %s" % (ticket, result))

        return ticket, result


    def respond(self, ticket, success):
        try:
            res = getURL(self.RESPOND_URL, post={"task_id": ticket, "key": self.get_config('passkey'),
                                                 "cv": 1 if success else 0})
        except BadHeader, e:
            self.log_error(_("Could not send response"), e)


    def captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.get_config('passkey'):
            return False

        if self.pyload.is_client_connected() and not self.get_config('force'):
            return False

        if self.get_credits() > 0:
            task.handler.append(self)
            task.data['service'] = self.get_class_name()
            task.setWaiting(100)
            self._process_captcha(task)

        else:
            self.log_info(_("Your %s account has not enough credits") % self.get_class_name())


    def captcha_correct(self, task):
        if task.data['service'] == self.get_class_name() and "ticket" in task.data:
            self.respond(task.data['ticket'], True)


    def captcha_invalid(self, task):
        if task.data['service'] == self.get_class_name() and "ticket" in task.data:
            self.respond(task.data['ticket'], False)


    @threaded
    def _process_captcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except BypassCaptchaException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
