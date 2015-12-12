# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay
# @interface-version: 0.1

import __builtin__

import threading
import traceback
import types

import SafeEval

from pyload.Thread import AddonThread
from pyload.misc import lock
from pyload.misc.decorators import try_catch


class AddonManager(object):
    """
    Manages addons, delegates and handles Events.

        Every plugin can define events, \
        but some very usefull events are called by the Core.
        Contrary to overwriting addon methods you can use event listener,
        which provides additional entry point in the control flow.
        Only do very short tasks or use threads.

        **Known Events:**
        Most addon methods exists as events. These are the additional known events.

        ======================= ============== ==================================
        Name                     Arguments      Description
        ======================= ============== ==================================
        download-preparing      fid            A download was just queued and will be prepared now.
        download-start          fid            A plugin will immediately starts the download afterwards.
        links-added             links, pid     Someone just added links, you are able to modify the links.
        all_downloads-processed                Every link was handled, pyload would idle afterwards.
        all_downloads-finished                 Every download in queue is finished.
        config-changed                          The config was changed via the api.
        pluginConfigChanged                    The plugin config changed, due to api or internal process.
        ======================= ============== ==================================

        | Notes:
        |    all_downloads-processed is *always* called before all_downloads-finished.
        |    config-changed is *always* called before pluginConfigChanged.
    """

    def __init__(self, core):
        self.pyload = core

        __builtin__.addonManager = self  #: needed to let addons register themself

        self.plugins = []
        self.pluginMap = {}
        self.methods = {}  #: dict of names and list of methods usable by rpc

        self.events = {}  #: contains events

        # registering callback for config event
        self.pyload.config.pluginCB = types.Method_type(self.dispatchEvent, "pluginConfigChanged", basestring)  #@TODO: Rename event pluginConfigChanged

        self.add_event("pluginConfigChanged", self.manageAddon)

        self.lock = threading.RLock()
        self.create_index()


    def addRPC(self, plugin, func, doc):
        plugin = plugin.rpartition(".")[2]
        doc = doc.strip() if doc else ""

        if plugin in self.methods:
            self.methods[plugin][func] = doc
        else:
            self.methods[plugin] = {func: doc}


    def callRPC(self, plugin, func, args, parse):
        if not args:
            args = ()
        if parse:
            args = tuple([SafeEval.const_eval(x) for x in args])
        plugin = self.pluginMap[plugin]
        f = getattr(plugin, func)
        return f(*args)


    def create_index(self):
        plugins  = []

        for type in ("addon", "hook"):
            actived     = []
            deactivated = []
            for pluginname in getattr(self.pyload.pluginManager, "%sPlugins" % type):
                try:
                    pluginClass = self.pyload.pluginManager.load_class(type, pluginname)
                    if not pluginClass:
                        continue

                    if self.pyload.config.get_plugin("%s_%s" % (pluginname, type), "activated"):
                        plugin = pluginClass(self.pyload, self)
                        plugins.append(plugin)

                        self.pluginMap[pluginClass.__name__] = plugin
                        if plugin.isActivated():
                            actived.append(pluginClass.__name)

                    else:
                        deactivated.append(pluginClass.__name__)

                except Exception:
                    self.pyload.log.warning(_("Failed activating %(name)s") % {"name": pluginname})
                    if self.pyload.debug:
                        traceback.print_exc()

            self.pyload.log.info(_("Activate %ss: %s") % (type, ", ".join(sorted(actived))))
            self.pyload.log.info(_("Deactivate %ss: %s") % (type, ", ".join(sorted(deactivated))))

        self.plugins = plugins


    def manage_addon(self, plugin, name, value):
        if name == "activated" and value:
            self.activate_addon(plugin)

        elif name == "activated" and not value:
            self.deactivate_addon(plugin)


    def activate_addon(self, pluginname):
        # check if already loaded
        for inst in self.plugins:
            if inst.__class__.__name__ == pluginname:
                return

        pluginClass = self.pyload.pluginManager.load_class("addon", pluginname)

        if not pluginClass:
            return

        self.pyload.log.debug("Activate addon: %s" % pluginname)

        addon = pluginClass(self.pyload, self)
        self.plugins.append(addon)
        self.pluginMap[pluginClass.__name__] = addon

        addon.activate()


    def deactivate_addon(self, pluginname):
        for plugin in self.plugins:
            if plugin.__class__.__name__ == pluginname:
                addon = plugin
                break
        else:
            return

        self.pyload.log.debug("Deactivate addon: %s" % pluginname)

        addon.deactivate()

        # remove periodic call
        self.pyload.log.debug("Removed callback: %s" % self.pyload.scheduler.remove_job(addon.cb))

        self.plugins.remove(addon)
        del self.pluginMap[addon.__class__.__name__]


    @try_catch
    def core_ready(self):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.activate()

        self.dispatch_event("addon-start")


    @try_catch
    def core_exiting(self):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.exit()

        self.dispatch_event("addon-exit")


    @lock
    def download_preparing(self, pyfile):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.downloadPreparing(pyfile)

        self.dispatch_event("download-preparing", pyfile)


    @lock
    def download_finished(self, pyfile):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.downloadFinished(pyfile)

        self.dispatch_event("download-finished", pyfile)


    @lock
    @try_catch
    def download_failed(self, pyfile):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.downloadFailed(pyfile)

        self.dispatch_event("download-failed", pyfile)


    @lock
    def package_finished(self, package):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.packageFinished(package)

        self.dispatch_event("package-finished", package)


    @lock
    def before_reconnecting(self, ip):
        for plugin in self.plugins:
            plugin.beforeReconnecting(ip)

        self.dispatch_event("beforeReconnecting", ip)


    @lock
    def after_reconnecting(self, ip, oldip):
        for plugin in self.plugins:
            if plugin.isActivated():
                plugin.afterReconnecting(ip, oldip)

        self.dispatch_event("afterReconnecting", ip, oldip)


    def start_thread(self, function, *args, **kwargs):
        return AddonThread(self.pyload.threadManager, function, args, kwargs)


    def active_plugins(self):
        """Returns all active plugins"""
        return [x for x in self.plugins if x.is_activated()]


    def get_all_info(self):
        """Returns info stored by addon plugins"""
        info = {}
        for name, plugin in self.pluginMap.iteritems():
            if plugin.info:
                # copy and convert so str
                info[name] = dict(
                    [(x, str(y) if not isinstance(y, basestring) else y) for x, y in plugin.info.iteritems()])
        return info


    def get_info(self, plugin):
        info = {}
        if plugin in self.pluginMap and self.pluginMap[plugin].info:
            info = dict((x, str(y) if not isinstance(y, basestring) else y)
                         for x, y in self.pluginMap[plugin].info.iteritems())
        return info


    def add_event(self, event, func):
        """Adds an event listener for event name"""
        if event in self.events:
            self.events[event].append(func)
        else:
            self.events[event] = [func]


    def remove_event(self, event, func):
        """Removes previously added event listener"""
        if event in self.events:
            self.events[event].remove(func)


    def dispatch_event(self, event, *args):
        """Dispatches event with args"""
        if event in self.events:
            for f in self.events[event]:
                try:
                    f(*args)
                except Exception, e:
                    self.pyload.log.warning("Error calling event handler %s: %s, %s, %s"
                                          % (event, f, args, str(e)))
                    if self.pyload.debug:
                        traceback.print_exc()
