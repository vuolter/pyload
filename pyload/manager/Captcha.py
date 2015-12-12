# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

import threading
import time
import traceback

from pyload.misc import encode


class CaptchaManager(object):

    def __init__(self, core):
        self.lock = threading.Lock()
        self.pyload = core
        self.tasks = []  #: task store, for outgoing tasks only
        self.ids = 0  #: only for internal purpose


    def new_task(self, img, format, file, result_type):
        task = CaptchaTask(self.ids, img, format, file, result_type)
        self.ids += 1
        return task


    def remove_task(self, task):
        self.lock.acquire()
        if task in self.tasks:
            self.tasks.remove(task)
        self.lock.release()


    def get_task(self):
        self.lock.acquire()
        for task in self.tasks:
            if task.status in ("waiting", "shared-user"):
                self.lock.release()
                return task
        self.lock.release()
        return None


    def get_task_byID(self, tid):
        self.lock.acquire()
        for task in self.tasks:
            if task.id == str(tid):  #: task ids are strings
                self.lock.release()
                return task
        self.lock.release()
        return None


    def handle_captcha(self, task, timeout=50):
        cli = self.pyload.is_client_connected()

        if cli:  #: client connected -> should solve the captcha
            task.setWaiting(timeout)  #: wait 50 sec for response

        for plugin in self.pyload.addonManager.active_plugins():
            try:
                plugin.captchaTask(task)
            except Exception:
                if self.pyload.debug:
                    traceback.print_exc()

        if task.handler or cli:  #: the captcha was handled
            self.tasks.append(task)
            return True
        task.error = _("No Client connected for captcha decrypting")
        return False


class CaptchaTask(object):

    def __init__(self, id, img, format, file, result_type='textual'):
        self.id = str(id)
        self.captchaImg = img
        self.captchaFormat = format
        self.captchaFile = file
        self.captchaResultType = result_type
        self.handler = []  #: the hook plugins that will take care of the solution
        self.result = None
        self.waitUntil = None
        self.error = None  #: error message
        self.status = "init"
        self.data = {}  #: handler can store data here


    def get_captcha(self):
        return self.captchaImg, self.captchaFormat, self.captchaResultType


    def set_result(self, text):
        if self.is_textual():
            self.result = text
        if self.is_positional():
            try:
                parts = text.split(',')
                self.result = (int(parts[0]), int(parts[1]))
            except Exception:
                self.result = None


    def get_result(self):
        return encode(self.result)


    def get_status(self):
        return self.status


    def set_waiting(self, sec):
        """Let the captcha wait secs for the solution"""
        self.waitUntil = max(time.time() + sec, self.waitUntil)
        self.status = "waiting"


    def is_waiting(self):
        if self.result or self.error or self.timed_out():
            return False
        else:
            return True


    def is_textual(self):
        """Returns if text is written on the captcha"""
        return self.captchaResultType == 'textual'


    def is_positional(self):
        """Returns if user have to click a specific region on the captcha"""
        return self.captchaResultType == 'positional'


    def set_wating_for_user(self, exclusive):
        if exclusive:
            self.status = "user"
        else:
            self.status = "shared-user"


    def timed_out(self):
        return time.time() > self.waitUntil


    def invalid(self):
        """Indicates the captcha was not correct"""
        for x in self.handler:
            x.captchaInvalid(self)


    def correct(self):
        for x in self.handler:
            x.captchaCorrect(self)


    def __str__(self):
        return "<CaptchaTask '%s'>" % self.id
