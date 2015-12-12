# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import random
import re
import subprocess
import threading
import time
import traceback

import pycurl

from pyload.Datatype import PyFile
from pyload.Thread import DecrypterThread, DownloadThread, InfoThread
from pyload.network.RequestFactory import getURL
from pyload.misc import free_space, lock


class ThreadManager(object):
    """Manages the download threads, assign jobs, reconnect etc"""

    def __init__(self, core):
        """Constructor"""
        self.pyload = core

        self.threads = []  #: thread list
        self.local_threads = []  #: addon+decrypter threads

        self.pause = True

        self.reconnecting = threading.Event()
        self.reconnecting.clear()
        self.downloaded = 0  #: number of files downloaded since last cleanup

        self.lock = threading.Lock()

        # some operations require to fetch url info from hoster, so we caching them so it wont be done twice
        # contains a timestamp and will be purged after timeout
        self.infoCache = {}

        # pool of ids for online check
        self.resultIDs = 0

        # threads which are fetching hoster results
        self.infoResults = {}
        # timeout for cache purge
        self.timestamp = 0

        pycurl.global_init(pycurl.GLOBAL_DEFAULT)

        for _i in xrange(0, self.pyload.config.get("download", "max_downloads")):
            self.create_thread()


    def create_thread(self):
        """Create a download thread"""

        thread = DownloadThread(self)
        self.threads.append(thread)


    def create_info_thread(self, data, pid):
        """
        start a thread whichs fetches online status and other infos
        data = [ .. () .. ]
        """
        self.timestamp = time.time() + 5 * 60

        InfoThread(self, data, pid)


    @lock
    def create_result_thread(self, data, add=False):
        """Creates a thread to fetch online status, returns result id"""
        self.timestamp = time.time() + 5 * 60

        rid = self.resultIDs
        self.resultIDs += 1

        InfoThread(self, data, rid=rid, add=add)

        return rid


    @lock
    def get_info_result(self, rid):
        """Returns result and clears it"""
        self.timestamp = time.time() + 5 * 60

        if rid in self.infoResults:
            data = self.infoResults[rid]
            self.infoResults[rid] = {}
            return data
        else:
            return {}


    @lock
    def set_info_results(self, rid, result):
        self.infoResults[rid].update(result)


    def get_active_files(self):
        active = [x.active for x in self.threads if x.active and isinstance(x.active, PyFile)]

        for t in self.local_threads:
            active.extend(t.getActiveFiles())

        return active


    def processing_ids(self):
        """Get a id list of all pyfiles processed"""
        return [x.id for x in self.get_active_files()]


    def work(self):
        """Run all task which have to be done (this is for repetivive call by core)"""
        try:
            self.try_reconnect()
        except Exception, e:
            self.pyload.log.error(_("Reconnect Failed: %s") % str(e))
            self.reconnecting.clear()
            if self.pyload.debug:
                traceback.print_exc()
        self.check_thread_count()

        try:
            self.assign_job()
        except Exception, e:
            self.pyload.log.warning("Assign job error", e)
            if self.pyload.debug:
                traceback.print_exc()

            time.sleep(0.5)
            self.assign_job()
            # it may be failed non critical so we try it again

        if (self.infoCache or self.infoResults) and self.timestamp < time.time():
            self.infoCache.clear()
            self.infoResults.clear()
            self.pyload.log.debug("Cleared Result cache")


    #--------------------------------------------------------------------------

    def try_reconnect(self):
        """Checks if reconnect needed"""

        if not (self.pyload.config.get("reconnect", "activated") and self.pyload.api.is_time_reconnect()):
            return False

        active = [x.active.plugin.wantReconnect and x.active.plugin.waiting for x in self.threads if x.active]

        if not (0 < active.count(True) == len(active)):
            return False

        if not os.path.exists(self.pyload.config.get("reconnect", "method")):
            if os.path.exists(os.path.join(pypath, self.pyload.config.get("reconnect", "method"))):
                self.pyload.config.set("reconnect", "method", os.path.join(pypath, self.pyload.config.get("reconnect", "method")))
            else:
                self.pyload.config.set("reconnect", "activated", False)
                self.pyload.log.warning(_("Reconnect script not found!"))
                return

        self.reconnecting.set()

        # Do reconnect
        self.pyload.log.info(_("Starting reconnect"))

        while [x.active.plugin.waiting for x in self.threads if x.active].count(True) != 0:
            time.sleep(0.25)

        oldip = self.getIP()

        self.pyload.addonManager.before_reconnecting(oldip)

        self.pyload.log.debug("Old IP: %s" % oldip)

        try:
            reconn = subprocess.Popen(self.pyload.config.get("reconnect", "method"), bufsize=-1, shell=True)  # , stdout=subprocess.PIPE)
        except Exception:
            self.pyload.log.warning(_("Failed executing reconnect script!"))
            self.pyload.config.set("reconnect", "activated", False)
            self.reconnecting.clear()
            if self.pyload.debug:
                traceback.print_exc()
            return

        reconn.wait()
        time.sleep(1)
        newip = self.getIP()
        self.pyload.addonManager.after_reconnecting(newip)

        self.pyload.log.info(_("Reconnected, new IP: %s") % newip)

        self.reconnecting.clear()


    def getIP(self):
        """Retrieve current ip"""
        services = [("http://automation.whatismyip.com/n09230945.asp", "(\S+)"),
                    ("http://checkip.dyndns.org/", ".*Current IP Address: (\S+)</body>.*")]

        ip = ""
        for _i in xrange(10):
            try:
                sv = random.choice(services)
                ip = getURL(sv[0])
                ip = re.match(sv[1], ip).group(1)
                break
            except Exception:
                ip = ""
                time.sleep(1)

        return ip


    #--------------------------------------------------------------------------

    def check_thread_count(self):
        """Checks if there are need for increasing or reducing thread count"""

        if len(self.threads) == self.pyload.config.get("download", "max_downloads"):
            return True
        elif len(self.threads) < self.pyload.config.get("download", "max_downloads"):
            self.create_thread()
        else:
            free = [x for x in self.threads if not x.active]
            if free:
                free[0].put("quit")


    def clean_pycurl(self):
        """Make a global curl cleanup (currently ununused)"""
        if self.processing_ids():
            return False
        pycurl.global_cleanup()
        pycurl.global_init(pycurl.GLOBAL_DEFAULT)
        self.downloaded = 0
        self.pyload.log.debug("Cleaned up pycurl")
        return True


    #--------------------------------------------------------------------------

    def assign_job(self):
        """Assing a job to a thread if possible"""

        if self.pause or not self.pyload.api.is_time_download():
            return

        # if self.downloaded > 20:
        #    if not self.clean_py_curl():
            return

        free = [x for x in self.threads if not x.active]

        inuse = set([((x.active.plugintype, x.active.pluginname), self.get_limit(x)) for x in self.threads if x.active and isinstance(x.active, PyFile) and x.active.has_plugin() and x.active.plugin.account])
        inuse = map(lambda x: ('.'.join(x[0]), x[1], len([y for y in self.threads if y.active and isinstance(y.active, PyFile) and y.active.plugintype == x[0][0] and y.active.pluginname == x[0][1]])), inuse)
        onlimit = [x[0] for x in inuse if x[1] > 0 and x[2] >= x[1]]

        occ = [x.active.plugintype + '.' + x.active.pluginname for x in self.threads if x.active and isinstance(x.active, PyFile) and x.active.has_plugin() and not x.active.plugin.multiDL] + onlimit

        occ.sort()
        occ = tuple(set(occ))
        job = self.pyload.files.get_job(occ)
        if job:
            try:
                job.initPlugin()
            except Exception, e:
                self.pyload.log.critical(str(e))
                if self.pyload.debug:
                    traceback.print_exc()
                job.setStatus("failed")
                job.error = str(e)
                job.release()
                return

            if job.plugin.getPluginType() == "hoster":
                spaceLeft = free_space(self.pyload.config.get("general", "download_folder")) / 1024 / 1024
                if spaceLeft < self.pyload.config.get("general", "min_free_space"):
                    self.pyload.log.warning(_("Not enough space left on device"))
                    self.pause = True

                if free and not self.pause:
                    thread = free[0]
                    # self.downloaded += 1

                    thread.put(job)
                else:
                    # put job back
                    if occ not in self.pyload.files.jobCache:
                        self.pyload.files.jobCache[occ] = []
                    self.pyload.files.jobCache[occ].append(job.id)

                    # check for decrypt jobs
                    job = self.pyload.files.get_decrypt_job()
                    if job:
                        job.initPlugin()
                        thread = DecrypterThread(self, job)
            else:
                thread = DecrypterThread(self, job)


    def get_limit(self, thread):
        limit = thread.active.plugin.account.getAccountData(thread.active.plugin.user)["options"].get("limitDL", ["0"])[0]
        return int(limit)


    def cleanup(self):
        """Do global cleanup, should be called when finished with pycurl"""
        pycurl.global_cleanup()
