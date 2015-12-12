# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

import time
import threading

from pyload.manager.Event import UpdateEvent
from pyload.misc import format_size, lock


statusMap = {
    "finished"     : 0,
    "offline"      : 1,
    "online"       : 2,
    "queued"       : 3,
    "skipped"      : 4,
    "waiting"      : 5,
    "temp. offline": 6,
    "starting"     : 7,
    "failed"       : 8,
    "aborted"      : 9,
    "decrypting"   : 10,
    "custom"       : 11,
    "downloading"  : 12,
    "processing"   : 13,
    "unknown"      : 14,
}


def set_size(self, value):
    self._size = int(value)


class PyFile(object):
    """
    Represents a file object at runtime
    """
    __slots__ = ("m", "id", "url", "name", "size", "_size", "status", "plugintype", "pluginname",
                 "packageid", "error", "order", "lock", "plugin", "waitUntil",
                 "active", "abort", "statusname", "reconnected", "progress",
                 "maxprogress", "pluginmodule", "pluginclass")


    def __init__(self, manager, id, url, name, size, status, error, plugin, package, order):
        self.pyload  = manager.pyload
        self.manager = manager

        self.id = int(id)
        self.url = url
        self.name = name
        self.size = size
        self.status = status
        self.plugintype, self.pluginname = plugin
        self.packageid = package  #: should not be used, use package() instead
        self.error = error
        self.order = order
        # database information ends here

        self.lock = threading.RLock()

        self.plugin = None
        # self.download = None

        self.waitUntil = 0  #: time.time() + time to wait

        # status attributes
        self.active = False  #: obsolete?
        self.abort = False
        self.reconnected = False

        self.statusname = None

        self.progress = 0
        self.maxprogress = 100

        self.manager.cache[int(id)] = self

    # will convert all sizes to ints
    size = property(lambda self: self._size, setSize)


    def __repr__(self):
        return "PyFile %s: %s@%s" % (self.id, self.name, self.pluginname)


    @lock
    def init_plugin(self):
        """Inits plugin instance"""
        if not self.plugin:
            self.pluginmodule = self.pyload.pluginManager.plugin_module(self.plugintype, self.pluginname)
            self.pluginclass  = self.pyload.pluginManager.pluginClass(self.plugintype, self.pluginname)
            self.plugin       = self.pluginclass(self)


    @lock
    def has_plugin(self):
        """
        Thread safe way to determine this file has initialized plugin attribute

        :return:
        """
        return hasattr(self, "plugin") and self.plugin


    def package(self):
        """Return package instance"""
        return self.manager.get_package(self.packageid)


    def set_status(self, status):
        self.status = statusMap[status]
        self.sync()  #@TODO: needed aslong no better job approving exists


    def set_custom_status(self, msg, status="processing"):
        self.statusname = msg
        self.set_status(status)


    def get_status_name(self):
        if self.status not in (13, 14) or not self.statusname:
            return self.manager.statusMsg[self.status]
        else:
            return self.statusname


    def has_status(self, status):
        return statusMap[status] == self.status


    def sync(self):
        """Sync PyFile instance with database"""
        self.manager.update_link(self)


    @lock
    def release(self):
        """Sync and remove from cache"""
        # file has valid package
        if self.packageid > 0:
            self.sync()

        if hasattr(self, "plugin") and self.plugin:
            self.plugin.clean()
            del self.plugin

        self.manager.release_link(self.id)


    def delete(self):
        """Delete pyfile from database"""
        self.manager.delete_link(self.id)


    def to_dict(self):
        """Return dict with all information for interface"""
        return self.to_db_dict()


    def to_db_dict(self):
        """
        Return data as dict for databse

        format:

        {
            id: {'url': url, 'name': name ... }
        }

        """
        return {
            self.id: {
                'id': self.id,
                'url': self.url,
                'name': self.name,
                'plugin': self.pluginname,
                'size': self.get_size(),
                'format_size': self.format_size(),
                'status': self.status,
                'statusmsg': self.get_status_name(),
                'package': self.packageid,
                'error': self.error,
                'order': self.order
            }
        }


    def abort_download(self):
        """Abort pyfile if possible"""
        while self.id in self.pyload.threadManager.processing_ids():
            self.abort = True
            if self.plugin and self.plugin.req:
                self.plugin.req.abort_downloads()
            time.sleep(0.1)

        self.abort = False
        if self.has_plugin() and self.plugin.req:
            self.plugin.req.abort_downloads()

        self.release()


    def finish_if_done(self):
        """Set status to finish and release file if every thread is finished with it"""

        if self.id in self.pyload.threadManager.processing_ids():
            return False

        self.set_status("finished")
        self.release()
        self.manager.check_all_links_finished()
        return True


    def check_if_processed(self):
        self.manager.check_all_links_processed(self.id)


    def format_wait(self):
        """Formats and return wait time in humanreadable format"""
        seconds = self.waitUntil - time.time()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)


    def format_size(self):
        """Formats size to readable format"""
        return format_size(self.get_size())


    def formatETA(self):
        """Formats eta to readable format"""
        seconds = self.getETA()

        if seconds < 0:
            return "00:00:00"

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)


    def get_speed(self):
        """Calculates speed"""
        try:
            return self.plugin.req.speed
        except Exception:
            return 0


    def getETA(self):
        """Gets established time of arrival"""
        try:
            return self.get_bytes_left() / self.get_speed()
        except Exception:
            return 0


    def get_bytes_left(self):
        """Gets bytes left"""
        try:
            return self.get_size() - self.plugin.req.arrived
        except Exception:
            return 0


    def get_percent(self):
        """Get % of download"""
        if self.status == 12:
            try:
                return self.plugin.req.percent
            except Exception:
                return 0
        else:
            return self.progress


    def get_size(self):
        """Get size of download"""
        try:
            if self.plugin.req.size:
                return self.plugin.req.size
            else:
                return self.size
        except Exception:
            return self.size


    def notify_change(self):
        e = UpdateEvent("file", self.id, "collector" if not self.package().queue else "queue")
        self.pyload.pullManager.add_event(e)


    def set_progress(self, value):
        if not value == self.progress:
            self.progress = value
            self.notify_change()
