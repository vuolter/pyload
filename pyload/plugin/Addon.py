# -*- coding: utf-8 -*-

import traceback

from pyload.plugin.Plugin import Plugin
from pyload.utils import has_method


class Expose(object):
    """Used for decoration to declare rpc services"""

    def __new__(cls, f, *args, **kwargs):
        addonManager.addRPC(f.__module__, f.func_name, f.func_doc)
        return f


def threaded(fn):

    def run(*args, **kwargs):
        addonManager.startThread(fn, *args, **kwargs)

    return run


class Addon(Plugin):
    __name    = "Addon"
    __type    = "addon"
    __version = "0.03"

    __config = []  #: [("name", "type", "desc", "default")]

    __description = """Base addon plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de"),
                     ("RaNaN", "RaNaN@pyload.org")]


    #: automatically register event listeners for functions, attribute will be deleted dont use it yourself
    event_map = {}

    # Deprecated alternative to event_map
    #: List of events the plugin can handle, name the functions exactly like eventname.
    event_list = []  #@NOTE: dont make duplicate entries in event_map


    def __init__(self, core, manager):
        #: Provide information in dict here, usable by API `getInfo`
        self.info = {}

        #: Callback of periodical job task, used by AddonManager
        self.cb = None
        self.interval = 60

        #: `AddonManager`
        self.manager = manager

        # register events
        if self.event_map:
            for event, funcs in self.event_map.iteritems():
                if type(funcs) in (list, tuple):
                    for f in funcs:
                        self.manager.addEvent(event, getattr(self, f))
                else:
                    self.manager.addEvent(event, getattr(self, funcs))

            # delete for various reasons
            self.event_map = None

        if self.event_list:
            self.logWarning(_("Plugin used deprecated `event_list`, use `event_map` instead"))

            for f in self.event_list:
                self.manager.addEvent(f, getattr(self, f))

            self.event_list = None

        self.setup()


    def initPeriodical(self, delay=0, threaded=False):
        self.cb = self.core.scheduler.addJob(max(0, delay), self._periodical, [threaded], threaded=threaded)


    def _periodical(self, threaded):
        if self.interval < 0:
            self.cb = None
            return

        try:
            self.periodical()

        except Exception, e:
            self.logError(_("Error executing addon: %s") % e)
            if self.core.debug:
                traceback.print_exc()

        self.cb = self.core.scheduler.addJob(self.interval, self._periodical, [threaded], threaded=threaded)


    def __repr__(self):
        return "<Addon %s>" % self.__name__


    def setup(self):
        """More init stuff if needed"""
        pass


    def deactivate(self):
        """Called when addon was deactivated"""
        if has_method(self.__class__, "unload"):
            self.logWarning(_("Deprecated method `unload`, use `deactivate` instead"))
            self.unload()


    #: Deprecated, use method `deactivate` instead
    def unload(self):
        pass


    def isActivated(self):
        """Checks if addon is activated"""
        return self.getConfig("activated")


    # Event methods - overwrite these if needed


    def activate(self):
        """Called when addon was activated"""
        if has_method(self.__class__, "coreReady"):
            self.logWarning(_("Deprecated method `coreReady`, use `activate` instead"))
            self.coreReady()


    #: Deprecated, use method `activate` instead
    def coreReady(self):
        pass


    def exit(self):
        """Called by core.shutdown just before pyLoad exit"""
        if has_method(self.__class__, "coreExiting"):
            self.coreExiting()


    #: Deprecated, use method `exit` instead
    def coreExiting(self):
        pass


    def downloadPreparing(self, pyfile):
        pass


    def downloadFinished(self, pyfile):
        pass


    def downloadFailed(self, pyfile):
        pass


    def packageFinished(self, pypack):
        pass


    def beforeReconnecting(self, ip):
        pass


    def afterReconnecting(self, ip, oldip):
        pass


    def periodical(self):
        pass


    def captchaTask(self, task):
        """New captcha task for the plugin, it MUST set the handler and timeout or will be ignored"""
        pass


    def captchaCorrect(self, task):
        pass


    def captchaInvalid(self, task):
        pass
