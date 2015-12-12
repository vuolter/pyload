# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

from pyload.manager.Event import UpdateEvent
from pyload.misc import safe_filename


class PyPackage(object):
    """Represents a package object at runtime"""

    def __init__(self, manager, id, name, folder, site, password, queue, order):
        self.pyload  = manager.pyload
        self.manager = manager
        self.manager.package_cache[int(id)] = self

        self.id = int(id)
        self.name = name
        self._folder = folder
        self.site = site
        self.password = password
        self.queue = queue
        self.order = order
        self.setFinished = False


    @property
    def folder(self):
        return safe_filename(self._folder)


    def to_dict(self):
        """
        Returns a dictionary representation of the data.

        :return: dict: {id: { attr: value }}
        """
        return {
            self.id: {
                'id': self.id,
                'name': self.name,
                'folder': self.folder,
                'site': self.site,
                'password': self.password,
                'queue': self.queue,
                'order': self.order,
                'links': {}
            }
        }


    def get_children(self):
        """Get information about contained links"""
        return self.manager.get_package_data(self.id)["links"]


    def sync(self):
        """Sync with db"""
        self.manager.update_package(self)


    def release(self):
        """Sync and delete from cache"""
        self.sync()
        self.manager.release_package(self.id)


    def delete(self):
        self.manager.delete_package(self.id)


    def notify_change(self):
        e = UpdateEvent("pack", self.id, "collector" if not self.queue else "queue")
        self.pyload.pullManager.add_event(e)
