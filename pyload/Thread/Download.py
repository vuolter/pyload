# -*- coding: utf-8 -*-
# @author: RaNaN

import Queue
import os
import sys
import time
import traceback

import pycurl

from pyload.Thread.Plugin import PluginThread
from pyload.plugin.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload


class Download_thread(Plugin_thread):
    """Thread for downloading files from 'real' hoster plugins"""

    def __init__(self, manager):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.queue = Queue.Queue()  #: job queue
        self.active = False

        self.start()


    #--------------------------------------------------------------------------

    def run(self):
        """Run method"""
        pyfile = None

        while True:
            del pyfile
            self.active = False  #: sets the thread inactive when it is ready to get next job
            self.active = self.queue.get()
            pyfile = self.active

            if self.active == "quit":
                self.active = False
                self.manager.threads.remove(self)
                return True

            try:
                if not pyfile.hasPlugin():
                    continue
                # this pyfile was deleted while queueing

                pyfile.plugin.checkForSameFiles(starting=True)
                self.pyload.log.info(_("Download starts: %s" % pyfile.name))

                # start download
                self.pyload.addonManager.download_preparing(pyfile)
                pyfile.error = ""
                pyfile.plugin.preprocessing(self)

                self.pyload.log.info(_("Download finished: %s") % pyfile.name)
                self.pyload.addonManager.download_finished(pyfile)
                self.pyload.files.check_package_finished(pyfile)

            except NotImplementedError:
                self.pyload.log.error(_("Plugin %s is missing a function.") % pyfile.pluginname)
                pyfile.setStatus("failed")
                pyfile.error = "Plugin does not work"
                self.clean(pyfile)
                continue

            except Abort:
                try:
                    self.pyload.log.info(_("Download aborted: %s") % pyfile.name)
                except Exception:
                    pass

                pyfile.setStatus("aborted")

                if self.pyload.debug:
                    traceback.print_exc()

                self.clean(pyfile)
                continue

            except Reconnect:
                self.queue.put(pyfile)
                # pyfile.req.clearCookies()

                while self.manager.reconnecting.is_set():
                    time.sleep(0.5)

                continue

            except Retry, e:
                reason = e.args[0]
                self.pyload.log.info(_("Download restarted: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": reason})
                self.queue.put(pyfile)
                continue

            except Fail, e:
                msg = e.args[0]

                if msg == "offline":
                    pyfile.setStatus("offline")
                    self.pyload.log.warning(_("Download is offline: %s") % pyfile.name)
                elif msg == "temp. offline":
                    pyfile.setStatus("temp. offline")
                    self.pyload.log.warning(_("Download is temporary offline: %s") % pyfile.name)
                else:
                    pyfile.setStatus("failed")
                    self.pyload.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": msg})
                    pyfile.error = msg

                if self.pyload.debug:
                    traceback.print_exc()

                self.pyload.addonManager.download_failed(pyfile)
                self.clean(pyfile)
                continue

            except pycurl.error, e:
                if len(e.args) == 2:
                    code, msg = e.args
                else:
                    code = 0
                    msg = e.args

                self.pyload.log.debug("pycurl exception %s: %s" % (code, msg))

                if code in (7, 18, 28, 52, 56):
                    self.pyload.log.warning(_("Couldn't connect to host or connection reset, waiting 1 minute and retry."))
                    wait = time.time() + 60

                    pyfile.waitUntil = wait
                    pyfile.setStatus("waiting")
                    while time.time() < wait:
                        time.sleep(1)
                        if pyfile.abort:
                            break

                    if pyfile.abort:
                        self.pyload.log.info(_("Download aborted: %s") % pyfile.name)
                        pyfile.setStatus("aborted")

                        self.clean(pyfile)
                    else:
                        self.queue.put(pyfile)

                    continue

                else:
                    pyfile.setStatus("failed")
                    self.pyload.log.error("pycurl error %s: %s" % (code, msg))
                    if self.pyload.debug:
                        traceback.print_exc()
                        self.write_debug_report(pyfile)

                    self.pyload.addonManager.download_failed(pyfile)

                self.clean(pyfile)
                continue

            except SkipDownload, e:
                pyfile.setStatus("skipped")

                self.pyload.log.info(_("Download skipped: %(name)s due to %(plugin)s") % {"name": pyfile.name, "plugin": e.message})

                self.clean(pyfile)

                self.pyload.files.check_package_finished(pyfile)

                self.active = False
                self.pyload.files.save()

                continue

            except Exception, e:
                pyfile.setStatus("failed")
                self.pyload.log.warning(_("Download failed: %(name)s | %(msg)s") % {"name": pyfile.name, "msg": str(e)})
                pyfile.error = str(e)

                if self.pyload.debug:
                    traceback.print_exc()
                    self.write_debug_report(pyfile)

                self.pyload.addonManager.download_failed(pyfile)
                self.clean(pyfile)
                continue

            finally:
                self.pyload.files.save()
                pyfile.checkIfProcessed()
                sys.exc_clear()

            # pyfile.plugin.req.clean()

            self.active = False
            pyfile.finishIfDone()
            self.pyload.files.save()


    def put(self, job):
        """Assing job to thread"""
        self.queue.put(job)


    def stop(self):
        """Stops the thread"""
        self.put("quit")
