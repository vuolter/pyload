# -*- coding: utf-8 -*-

import traceback

from pyload.plugin.Plugin import Base
from pyload.misc import has_method


class Expose(object):
    """Used for decoration to declare rpc services"""

    def __new__(cls, f, *args, **kwargs):
        addonManager.addRPC(f.__module__, f.func_name, f.func_doc)
        return f


def threaded(fn):

    def run(*args, **kwargs):
        addonManager.startThread(fn, *args, **kwargs)

    return run


class Addon(Base):
    __name    = "Addon"
    __type    = "addon"
    __version = "0.01"

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
        Base.__init__(self, core)

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
                        self.manager.add_event(event, getattr(self, f))
                else:
                    self.manager.add_event(event, getattr(self, funcs))

            # delete for various reasons
            self.event_map = None

        if self.event_list:
            self.log_warning(_("Plugin used deprecated `event_list`, use `event_map` instead"))

            for f in self.event_list:
                self.manager.add_event(f, getattr(self, f))

            self.event_list = None

        self.setup()


    def init_periodical(self, delay=0, threaded=False):
        self.cb = self.pyload.scheduler.add_job(max(0, delay), self._periodical, [threaded], threaded=threaded)


    def _periodical(self, threaded):
        if self.interval < 0:
            self.cb = None
            return

        try:
            self.periodical()

        except Exception, e:
            self.log_error(_("Error executing addon: %s") % e)
            if self.pyload.debug:
                traceback.print_exc()

        self.cb = self.pyload.scheduler.add_job(self.interval, self._periodical, [threaded], threaded=threaded)


    def __repr__(self):
        return "<Addon %s>" % self.get_class_name()


    def setup(self):
        """More init stuff if needed"""
        pass


    def deactivate(self):
        """Called when addon was deactivated"""
        if has_method(self.__class__, "unload"):
            self.log_warning(_("Deprecated method `unload`, use `deactivate` instead"))
            self.unload()


    def unload(self):  #: Deprecated, use method `deactivate` instead
        pass


    def is_activated(self):
        """Checks if addon is activated"""
        return self.get_config("activated")


    # Event methods - overwrite these if needed


    def activate(self):
        """Called when addon was activated"""
        if has_method(self.__class__, "coreReady"):
            self.log_warning(_("Deprecated method `coreReady`, use `activate` instead"))
            self.core_ready()


    def core_ready(self):  #: Deprecated, use method `activate` instead
        pass


    def exit(self):
        """Called by pyload.shutdown just before pyLoad exit"""
        if has_method(self.__class__, "coreExiting"):
            self.core_exiting()


    def core_exiting(self):  #: Deprecated, use method `exit` instead
        pass


    def download_preparing(self, pyfile):
        pass


    def download_finished(self, pyfile):
        pass


    def download_failed(self, pyfile):
        pass


    def package_finished(self, pypack):
        pass


    def before_reconnecting(self, ip):
        pass


    def after_reconnecting(self, ip, oldip):
        pass


    def periodical(self):
        pass


    def captcha_task(self, task):
        """New captcha task for the plugin, it MUST set the handler and timeout or will be ignored"""
        pass


    def captcha_correct(self, task):
        pass


    def captcha_invalid(self, task):
        pass
