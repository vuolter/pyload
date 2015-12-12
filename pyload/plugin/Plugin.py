# -*- coding: utf-8 -*-

from __future__ import with_statement

import traceback

import itertools
import os
import random
import re
import time
import urllib
import urlparse

if os.name != "nt":
    import grp
    import pwd

from pyload.misc import fs_decode, fs_encode, safe_filename, fs_join, encode


def chunks(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


class Abort(Exception):
    """ raised when aborted """


class Fail(Exception):
    """ raised when failed """


class Reconnect(Exception):
    """ raised when reconnected """


class Retry(Exception):
    """ raised when start again from beginning """


class SkipDownload(Exception):
    """ raised when download should be skipped """


class Base(object):
    """
    A Base class with log/config/db methods *all* plugin types can use
    """


    def __init__(self, core):
        #: Core instance
        self.core = core


    def _log(self, type, args):
        msg = " | ".join([encode(str(a)).strip() for a in args if a])
        logger = getattr(self.core.log, type)
        logger("%s: %s" % (self.get_class_name(), msg or _("%s MARK" % type.upper())))


    def log_debug(self, *args):
        if self.core.debug:
            return self._log("debug", args)


    def log_info(self, *args):
        return self._log("info", args)


    def log_warning(self, *args):
        return self._log("warning", args)


    def log_error(self, *args):
        return self._log("error", args)


    def log_critical(self, *args):
        return self._log("critical", args)


    def get_plugin_type(self):
        return getattr(self, "_%s__type" % self.get_class_name())


    @classmethod
    def get_class_name(cls):
        return cls.__name__


    def get_plugin_conf_section(self):
        return "%s_%s" % (self.get_class_name(), getattr(self, "_%s__type" % self.get_class_name()))

    #: Deprecated method


    def set_conf(self, option, value):
        """ see `setConfig` """
        self.set_config(option, value)


    def set_config(self, option, value):
        """ Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.core.config.set_plugin(self.get_plugin_conf_section(), option, value)

    #: Deprecated method


    def get_conf(self, option):
        """ see `getConfig` """
        return self.core.config.get_plugin(self.get_plugin_conf_section(), option)


    def get_config(self, option):
        """ Returns config value for current plugin

        :param option:
        :return:
        """
        return self.core.config.get_plugin(self.get_plugin_conf_section(), option)


    def set_storage(self, key, value):
        """ Saves a value persistently to the database """
        self.core.db.set_storage(self.get_plugin_conf_section(), key, value)


    def store(self, key, value):
        """ same as `setStorage` """
        self.core.db.set_storage(self.get_plugin_conf_section(), key, value)


    def get_storage(self, key=None, default=None):
        """ Retrieves saved value or dict of all saved entries if key is None """
        if key:
            return self.core.db.get_storage(self.get_plugin_conf_section(), key) or default
        return self.core.db.get_storage(self.get_plugin_conf_section(), key)


    def retrieve(self, *args, **kwargs):
        """ same as `getStorage` """
        return self.get_storage(*args, **kwargs)


    def del_storage(self, key):
        """ Delete entry in db """
        self.core.db.del_storage(self.get_class_name(), key)


class Plugin(Base):
    """
    Base plugin for hoster/crypter.
    Overwrite `process` / `decrypt` in your subclassed plugin.
    """
    __name    = "Plugin"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'^unmatchable$'
    __config  = []  #: [("name", "type", "desc", "default")]

    __description = """Base plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                     ("spoob", "spoob@pyload.org"),
                     ("mkaay", "mkaay@mkaay.de")]

    info = {}  #: file info dict


    def __init__(self, pyfile):
        Base.__init__(self, pyfile.m.core)

        #: engage wan reconnection
        self.wantReconnect = False

        #: enable simultaneous processing of multiple downloads
        self.multiDL = True
        self.limitDL = 0

        #: chunk limit
        self.chunkLimit = 1
        self.resumeDownload = False

        #: time.time() + wait in seconds
        self.waitUntil = 0
        self.waiting = False

        #: captcha reader instance
        self.ocr = None

        #: account handler instance, see :py:class:`Account`
        self.account = pyfile.m.core.account_manager.get_account_plugin(self.get_class_name())

        #: premium status
        self.premium = False
        #: username/login
        self.user = None

        if self.account and not self.account.can_use():
            self.account = None

        if self.account:
            self.user, data = self.account.select_account()
            #: Browser instance, see `network.Browser`
            self.req = self.account.get_account_request(self.user)
            self.chunkLimit = -1  #: chunk limit, -1 for unlimited
            #: enables resume (will be ignored if server dont accept chunks)
            self.resumeDownload = True
            self.multiDL = True  #: every hoster with account should provide multiple downloads
            #: premium status
            self.premium = self.account.is_premium(self.user)
        else:
            self.req = pyfile.m.core.request_factory.get_request(self.get_class_name())

        #: associated pyfile instance, see `PyFile`
        self.pyfile = pyfile

        self.thread = None  #: holds thread in future

        #: location where the last call to download was saved
        self.lastDownload = ""
        #: re match of the last call to `checkDownload`
        self.lastCheck = None

        #: js engine, see `JsEngine`
        self.js = self.core.js

        #: captcha task
        self.cTask = None

        self.html = None  #@TODO: Move to hoster class in 0.4.10
        self.retries = 0

        self.init()


    def get_chunk_count(self):
        if self.chunkLimit <= 0:
            return self.core.config.get("download", "chunks")
        return min(self.core.config.get("download", "chunks"), self.chunkLimit)


    def __call__(self):
        return self.get_class_name()


    def init(self):
        """initialize the plugin (in addition to `__init__`)"""
        pass


    def setup(self):
        """ setup for enviroment and other things, called before downloading (possibly more than one time)"""
        pass


    def preprocessing(self, thread):
        """ handles important things to do before starting """
        self.thread = thread

        if self.account:
            self.account.check_login(self.user)
        else:
            self.req.clear_cookies()

        self.setup()

        self.pyfile.set_status("starting")

        return self.process(self.pyfile)


    def process(self, pyfile):
        """the 'main' method of every plugin, you **have to** overwrite it"""
        raise NotImplementedError


    def reset_account(self):
        """ dont use account and retry download """
        self.account = None
        self.req = self.core.requestFactory.get_request(self.get_class_name())
        self.retry()


    def checksum(self, local_file=None):
        """
        return codes:
        0  - checksum ok
        1  - checksum wrong
        5  - can't get checksum
        10 - not implemented
        20 - unknown error
        """
        #@TODO checksum check addon

        return True, 10


    def set_reconnect(self, reconnect):
        reconnect = bool(reconnect)
        self.log_debug("Set wantReconnect to: %s (previous: %s)" % (reconnect, self.wantReconnect))
        self.wantReconnect = reconnect


    def set_wait(self, seconds, reconnect=None):
        """Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        wait_time  = int(seconds) + 1
        wait_until = time.time() + wait_time

        self.log_debug("Set waitUntil to: %f (previous: %f)" % (wait_until, self.pyfile.waitUntil),
                      "Wait: %d seconds" % wait_time)

        self.pyfile.waitUntil = wait_until

        if reconnect is not None:
            self.set_reconnect(reconnect)


    def wait(self, seconds=None, reconnect=None):
        """ waits the time previously set """

        pyfile = self.pyfile

        if seconds is not None:
            self.set_wait(seconds)

        if reconnect is not None:
            self.set_reconnect(reconnect)

        self.waiting = True

        status = pyfile.status
        pyfile.set_status("waiting")

        self.log_info(_("Wait: %d seconds") % (pyfile.waitUntil - time.time()),
                     _("Reconnect: %s")    % self.wantReconnect)

        if self.account:
            self.log_debug("Ignore reconnection due account logged")

            while pyfile.waitUntil > time.time():
                if pyfile.abort:
                    self.abort()

                time.sleep(1)
        else:
            while pyfile.waitUntil > time.time():
                self.thread.m.reconnecting.wait(2)

                if pyfile.abort:
                    self.abort()

                if self.thread.m.reconnecting.is_set():
                    self.waiting = False
                    self.wantReconnect = False
                    raise Reconnect

                time.sleep(1)

        self.waiting = False

        pyfile.status = status


    def fail(self, reason):
        """ fail and give reason """
        raise Fail(reason)


    def abort(self, reason=""):
        """ abort and give reason """
        if reason:
            self.pyfile.error = str(reason)
        raise Abort


    def error(self, reason="", type=""):
        if not reason and not type:
            type = "unknown"

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += (": %s" % reason.strip()) if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(msg)


    def offline(self, reason=""):
        """ fail and indicate file is offline """
        if reason:
            self.pyfile.error = str(reason)
        raise Fail("offline")


    def temp_offline(self, reason=""):
        """ fail and indicates file ist temporary offline, the core may take consequences """
        if reason:
            self.pyfile.error = str(reason)
        raise Fail("temp. offline")


    def retry(self, max_tries=5, wait_time=1, reason=""):
        """Retries and begin again from the beginning

        :param max_tries: number of maximum retries
        :param wait_time: time to wait in seconds
        :param reason: reason for retrying, will be passed to fail if max_tries reached
        """
        if 0 < max_tries <= self.retries:
            self.error(reason or _("Max retries reached"), "retry")

        self.wait(wait_time, False)

        self.retries += 1
        raise Retry(reason)


    def invalid_captcha(self):
        self.log_error(_("Invalid captcha"))
        if self.cTask:
            self.cTask.invalid()


    def correct_captcha(self):
        self.log_info(_("Correct captcha"))
        if self.cTask:
            self.cTask.correct()


    def decrypt_captcha(self, url, get={}, post={}, cookies=False, force_user=False, imgtype='jpg',
                       result_type='textual', timeout=290):
        """ Loads a captcha and decrypts it with ocr, plugin, user input

        :param url: url of captcha image
        :param get: get part for request
        :param post: post part for request
        :param cookies: True if cookies should be enabled
        :param forceUser: if True, ocr is not used
        :param imgtype: Type of the Image
        :param result_type: 'textual' if text is written on the captcha\
        or 'positional' for captcha where the user have to click\
        on a specific region on the captcha

        :return: result of decrypting
        """

        img = self.load(url, get=get, post=post, cookies=cookies)

        id = ("%.2f" % time.time())[-6:].replace(".", "")

        with open(os.path.join("tmp", "tmpCaptcha_%s_%s.%s" % (self.get_class_name(), id, imgtype)), "wb") as tmpCaptcha:
            tmpCaptcha.write(img)

        has_plugin = self.get_class_name() in self.core.pluginManager.ocrPlugins

        if self.core.captcha:
            Ocr = self.core.pluginManager.load_class("ocr", self.get_class_name())
        else:
            Ocr = None

        if Ocr and not forceUser:
            time.sleep(random.randint(3000, 5000) / 1000.0)
            if self.pyfile.abort:
                self.abort()

            ocr = Ocr()
            result = ocr.get_captcha(tmpCaptcha.name)
        else:
            captchaManager = self.core.captchaManager
            task = captchaManager.newTask(img, imgtype, tmpCaptcha.name, result_type)
            self.cTask = task
            captchaManager.handleCaptcha(task, timeout)

            while task.isWaiting():
                if self.pyfile.abort:
                    captchaManager.removeTask(task)
                    self.abort()
                time.sleep(1)

            captchaManager.removeTask(task)

            if task.error and has_plugin:  #: ignore default error message since the user could use OCR
                self.fail(_("Pil and tesseract not installed and no Client connected for captcha decrypting"))
            elif task.error:
                self.fail(task.error)
            elif not task.result:
                self.fail(_("No captcha result obtained in appropiate time by any of the plugins"))

            result = task.result
            self.log_debug("Received captcha result: %s" % result)

        if not self.core.debug:
            try:
                os.remove(tmpCaptcha.name)
            except Exception:
                pass

        return result


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=False, follow_location=True, save_cookies=True):
        """Load content at url and returns it

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param just_header: If True only the header will be retrieved and returned as dict
        :param decode: Wether to decode the output according to http header, should be True in most cases
        :param follow_location: If True follow location else not
        :param save_cookies: If True saves received cookies else discard them
        :return: Loaded content
        """
        if self.pyfile.abort:
            self.abort()

        if not url:
            self.fail(_("No url given"))

        url = urllib.unquote(encode(url).strip())  #@NOTE: utf8 vs decode -> please use decode attribute in all future plugins

        if self.core.debug:
            self.log_debug("Load url: " + url, *["%s=%s" % (key, val) for key, val in locals().iteritems() if key not in ("self", "url")])

        res = self.req.load(url, get, post, ref, cookies, just_header, decode=decode, follow_location=follow_location, save_cookies=save_cookies)

        if decode:
            res = encode(res)

        if self.core.debug:
            import inspect

            frame = inspect.currentframe()
            framefile = fs_join("tmp", self.get_class_name(), "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))
            try:
                if not os.path.exists(os.path.join("tmp", self.get_class_name())):
                    os.makedirs(os.path.join("tmp", self.get_class_name()))

                with open(framefile, "wb") as f:
                    del frame  #: delete the frame or it wont be cleaned
                    f.write(res)
            except IOError, e:
                self.log_error(e)

        if just_header:
            # parse header
            header = {"code": self.req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                key, none, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()

                if key in header:
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res


    def download(self, url, get={}, post={}, ref=True, cookies=True, disposition=False):
        """Downloads the content at url to download folder

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param disposition: if True and server provides content-disposition header\
        the filename will be changed if needed
        :return: The location where the file was saved
        """
        if self.pyfile.abort:
            self.abort()

        if not url:
            self.fail(_("No url given"))

        url = urllib.unquote(encode(url).strip())

        if self.core.debug:
            self.log_debug("Download url: " + url, *["%s=%s" % (key, val) for key, val in locals().iteritems() if key not in ("self", "url")])

        self.check_for_same_files()

        self.pyfile.set_status("downloading")

        if disposition:
            self.pyfile.name = urlparse.urlparse(url).path.split('/')[-1] or self.pyfile.name

        download_folder = self.core.config.get("general", "download_folder")

        location = fs_join(download_folder, self.pyfile.package().folder)

        if not os.path.exists(location):
            try:
                os.makedirs(location, int(self.core.config.get("permission", "folder"), 8))

                if self.core.config.get("permission", "change_dl") and os.name != "nt":
                    uid = pwd.getpwnam(self.core.config.get("permission", "user"))[2]
                    gid = grp.getgrnam(self.core.config.get("permission", "group"))[2]
                    os.chown(location, uid, gid)

            except Exception, e:
                self.fail(e)

        # convert back to unicode
        location = fs_decode(location)
        name = safe_filename(self.pyfile.name)

        filename = os.path.join(location, name)

        self.core.addonManager.dispatch_event("download-start", self.pyfile, url, filename)

        try:
            newname = self.req.http_download(url, filename, get=get, post=post, ref=ref, cookies=cookies,
                                            chunks=self.get_chunk_count(), resume=self.resumeDownload,
                                            progressNotify=self.pyfile.setProgress, disposition=disposition)
        finally:
            self.pyfile.size = self.req.size

        if newname:
            newname = urlparse.urlparse(newname).path.split('/')[-1]

            if disposition and newname != name:
                self.log_info(_("%(name)s saved as %(newname)s") % {"name": name, "newname": newname})
                self.pyfile.name = newname
                filename = os.path.join(location, newname)

        fs_filename = fs_encode(filename)

        if self.core.config.get("permission", "change_file"):
            try:
                os.chmod(fs_filename, int(self.core.config.get("permission", "file"), 8))
            except Exception, e:
                self.log_warning(_("Setting file mode failed"), e)

        if self.core.config.get("permission", "change_dl") and os.name != "nt":
            try:
                uid = pwd.getpwnam(self.core.config.get("permission", "user"))[2]
                gid = grp.getgrnam(self.core.config.get("permission", "group"))[2]
                os.chown(fs_filename, uid, gid)

            except Exception, e:
                self.log_warning(_("Setting User and Group failed"), e)

        self.lastDownload = filename
        return self.lastDownload


    def check_download(self, rules, api_size=0, max_size=50000, delete=True, read_size=0):
        """ checks the content of the last downloaded file, re match is saved to `lastCheck`

        :param rules: dict with names and rules to match (compiled regexp or strings)
        :param api_size: expected file size
        :param max_size: if the file is larger then it wont be checked
        :param delete: delete if matched
        :param read_size: amount of bytes to read from files larger then max_size
        :return: dictionary key of the first rule that matched
        """
        lastDownload = fs_encode(self.lastDownload)
        if not os.path.exists(lastDownload):
            return None

        size = os.stat(lastDownload)
        size = size.st_size

        if api_size and api_size <= size:
            return None
        elif size > max_size and not read_size:
            return None
        self.log_debug("Download Check triggered")

        with open(lastDownload, "rb") as f:
            content = f.read(read_size if read_size else -1)

        # produces encoding errors, better log to other file in the future?
        # self.log_debug("Content: %s" % content)
        for name, rule in rules.iteritems():
            if isinstance(rule, basestring):
                if rule in content:
                    if delete:
                        os.remove(lastDownload)
                    return name
            elif hasattr(rule, "search"):
                m = rule.search(content)
                if m:
                    if delete:
                        os.remove(lastDownload)
                    self.lastCheck = m
                    return name


    def get_password(self):
        """ get the password the user provided in the package"""
        password = self.pyfile.package().password
        if not password:
            return ""
        return password


    def check_for_same_files(self, starting=False):
        """ checks if same file was/is downloaded within same package

        :param starting: indicates that the current download is going to start
        :raises Skip:
        """

        pack = self.pyfile.package()

        for pyfile in self.core.files.cache.values():
            if pyfile != self.pyfile and pyfile.name == self.pyfile.name and pyfile.package().folder == pack.folder:
                if pyfile.status in (0, 12):  #: finished or downloading
                    raise Skip(pyfile.pluginname)
                elif pyfile.status in (5, 7) and starting:  #: a download is waiting/starting and was appenrently started before
                    raise Skip(pyfile.pluginname)

        download_folder = self.core.config.get("general", "download_folder")
        location = fs_join(download_folder, pack.folder, self.pyfile.name)

        if starting and self.core.config.get("download", "skip_existing") and os.path.exists(location):
            size = os.stat(location).st_size
            if size >= self.pyfile.size:
                raise Skip("File exists")

        pyfile = self.core.db.find_duplicates(self.pyfile.id, self.pyfile.package().folder, self.pyfile.name)
        if pyfile:
            if os.path.exists(location):
                raise Skip(pyfile[0])

            self.log_debug("File %s not skipped, because it does not exists." % self.pyfile.name)


    def clean(self):
        """ clean everything and remove references """
        if hasattr(self, "pyfile"):
            del self.pyfile

        if hasattr(self, "req"):
            self.req.close()
            del self.req

        if hasattr(self, "thread"):
            del self.thread

        if hasattr(self, "html"):
            del self.html
