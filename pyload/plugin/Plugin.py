# -*- coding: utf-8 -*-

from __future__ import with_statement

import itertools
import os
import random
import re
import time
import traceback
import urllib
import urlparse

if os.name != "nt":
    import grp
    import pwd

from pyload.utils import fs_decode, fs_encode, safe_filename, fs_join, encode


class Abort(Exception):
    """Raised when aborted"""


class Fail(Exception):
    """Raised when failed"""


class Reconnect(Exception):
    """Raised when reconnected"""


class Retry(Exception):
    """Raised when start again from beginning"""


class SkipDownload(Exception):
    """Raised when download should be skipped"""


class Plugin(Plugin):
    """
    A Base class with log/config/db methods *all* plugin types can use
    """

    __name    = "Plugin"
    __type    = "hoster"
    __version = "0.08"

    __pattern = r'^unmatchable$'
    __config  = []  #: [("name", "type", "desc", "default")]

    __description = """Base plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                     ("spoob", "spoob@pyload.org"),
                     ("mkaay", "mkaay@mkaay.de")]


    def __init__(self, core):
        #: Core instance
        self.core = core


    def __call__(self):
        return self.__name__


    def _log(self, type, args):
        msg = " | ".join([encode(str(a)).strip() for a in args if a])
        logger = getattr(self.core.log, type)
        logger("%s: %s" % (self.__name, msg or _("%s MARK" % type.upper())))


    def logDebug(self, *args):
        if self.core.debug:
            return self._log("debug", args)


    def logInfo(self, *args):
        return self._log("info", args)


    def logWarning(self, *args):
        return self._log("warning", args)


    def logError(self, *args):
        return self._log("error", args)


    def logCritical(self, *args):
        return self._log("critical", args)


    def getPluginType(self):
        return getattr(self, "_%s__type" % self.__name__)


    def getPluginConfSection(self):
        return "%s_%s" % (self.__name__, getattr(self, "_%s__type" % self.__name__))


    def setConfig(self, option, value):
        """
        Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.core.config.setPlugin(self.getPluginConfSection(), option, value)


    #: Deprecated method
    def setConf(self, *args, **kwargs):
        """See `setConfig`"""
        return self.setConfig(*args, **kwargs)


    def getConfig(self, option):
        """
        Returns config value for current plugin

        :param option:
        :return:
        """
        return self.core.config.getPlugin(self.getPluginConfSection(), option)


    #: Deprecated method
    def getConf(self, *args, **kwargs):
        """See `getConfig`"""
        return self.getConfig(*args, **kwargs)


    def store(self, key, value):
        """Saves a value persistently to the database"""
        self.core.db.setStorage(self.getPluginConfSection(), key, value)


    #: Deprecated method
    def setStorage(self, *args, **kwargs):
        """Same as `setStorage`"""
        return self.store(*args, **kwargs)


    def retrieve(self, key, default=None):
        """Retrieves saved value or dict of all saved entries if key is None"""
        return self.core.db.getStorage(self.getPluginConfSection(), key) or default


    #: Deprecated method
    def getStorage(self, *args, **kwargs):
        """Same as `getStorage`"""
        return self.retrieve(*args, **kwargs)


    def delStorage(self, key):
        """Delete entry in db"""
        self.core.db.delStorage(self.__name__, key)


    def fail(self, reason):
        """Fail and give reason"""
        raise Fail(reason)


    def error(self, reason="", type=""):
        if not reason and not type:
            type = "unknown"

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += (": %s" % reason.strip()) if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(msg)
