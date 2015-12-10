# -*- coding: utf-8 -*-

from __future__ import with_statement

import base64
import uuid

import pycurl

from pyload.network.HTTPRequest import BadHeader
from pyload.network.RequestFactory import getURL, getRequest
from pyload.plugin.Hook import Hook, threaded


class Expert_decoders(Hook):
    __name    = "ExpertDecoders"
    __type    = "hook"
    __version = "0.04"

    __config = [("force", "bool", "Force CT even if client is connected", False),
                ("passkey", "password", "Access key", "")]

    __description = """Send captchas to expertdecoders.com"""
    __license     = "GPLv3"
    __authors     = [("RaNaN"   , "RaNaN@pyload.org"   ),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://www.fasttypers.org/imagepost.ashx"


    def activate(self):
        if self.get_config('ssl'):
            self.API_URL = self.API_URL.replace("http://", "https://")


    def get_credits(self):
        res = getURL(self.API_URL, post={"key": self.get_config('passkey'), "action": "balance"})

        if res.isdigit():
            self.log_info(_("%s credits left") % res)
            self.info['credits'] = credits = int(res)
            return credits
        else:
            self.log_error(res)
            return 0


    @threaded
    def _process_captcha(self, task):
        task.data['ticket'] = ticket = uuid.uuid4()
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()

        req = getRequest()
        # raise timeout threshold
        req.c.setopt(pycurl.LOW_SPEED_TIME, 80)

        try:
            result = req.load(self.API_URL,
                              post={'action'     : "upload",
                                    'key'        : self.get_config('passkey'),
                                    'file'       : base64.b64encode(data),
                                    'gen_task_id': ticket})
        finally:
            req.close()

        self.log_debug("Result %s : %s" % (ticket, result))
        task.setResult(result)


    def captcha_task(self, task):
        if not task.isTextual():
            return False

        if not self.get_config('passkey'):
            return False

        if self.pyload.is_client_connected() and not self.get_config('force'):
            return False

        if self.get_credits() > 0:
            task.handler.append(self)
            task.setWaiting(100)
            self._process_captcha(task)

        else:
            self.log_info(_("Your ExpertDecoders Account has not enough credits"))


    def captcha_invalid(self, task):
        if "ticket" in task.data:

            try:
                res = getURL(self.API_URL,
                             post={'action': "refund", 'key': self.get_config('passkey'), 'gen_task_id': task.data['ticket']})
                self.log_info(_("Request refund"), res)

            except BadHeader, e:
                self.log_error(_("Could not send refund request"), e)
