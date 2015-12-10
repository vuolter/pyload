# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

import threading

from pyload.Datatype import PyFile, PyPackage
from pyload.Database import DatabaseBackend, style
from pyload.manager.Event import InsertEvent, ReloadAllEvent, RemoveEvent, UpdateEvent
from pyload.utils import format_size, lock

try:
    from pysqlite2 import dbapi2 as sqlite3
except Exception:
    import sqlite3


class File_handler(object):
    """Handles all request made to obtain information,
    modify status or other request for links or packages"""

    def __init__(self, core):
        """Constructor"""
        self.pyload = core

        # translations
        self.statusMsg = [_("finished"), _("offline"), _("online"), _("queued"), _("skipped"), _("waiting"),
                          _("temp. offline"), _("starting"), _("failed"), _("aborted"), _("decrypting"), _("custom"),
                          _("downloading"), _("processing"), _("unknown")]

        self.cache = {}  #: holds instances for files
        self.packageCache = {}  #: same for packages
        #@TODO: purge the cache

        self.jobCache = {}

        self.lock = threading.RLock()  #@TODO: should be a Lock w/o R
        # self.lock._Verbose__verbose = True

        self.filecount = -1  #: if an invalid value is set get current value from db
        self.queuecount = -1  #: number of package to be loaded
        self.unchanged = False  #: determines if any changes was made since last call

        self.db = self.pyload.db


    def change(func):


        def new(*args):
            args[0].unchanged = False
            args[0].filecount = -1
            args[0].queuecount = -1
            args[0].jobCache = {}
            return func(*args)

        return new


    #--------------------------------------------------------------------------

    def save(self):
        """Saves all data to backend"""
        self.db.commit()


    #--------------------------------------------------------------------------

    def sync_save(self):
        """Saves all data to backend and waits until all data are written"""
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            pyfile.sync()

        pypacks = self.packageCache.values()
        for pypack in pypacks:
            pypack.sync()

        self.db.sync_save()


    @lock
    def get_complete_data(self, queue=1):
        """Gets a complete data representation"""

        data = self.db.get_all_links(queue)
        packs = self.db.get_all_packages(queue)

        data.update([(x.id, x.toDbDict()[x.id]) for x in self.cache.values()])

        for x in self.packageCache.itervalues():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.toDict()[x.id])

        for key, value in data.iteritems():
            if value['package'] in packs:
                packs[value['package']]['links'][key] = value

        return packs


    @lock
    def get_info_data(self, queue=1):
        """Gets a data representation without links"""

        packs = self.db.get_all_packages(queue)
        for x in self.packageCache.itervalues():
            if x.queue != queue or x.id not in packs:
                continue
            packs[x.id].update(x.toDict()[x.id])

        return packs


    @lock
    @change
    def add_links(self, urls, package):
        """Adds links"""

        self.pyload.addonManager.dispatch_event("links-added", urls, package)

        data = self.pyload.pluginManager.parse_urls(urls)

        self.db.add_links(data, package)
        self.pyload.threadManager.create_info_thread(data, package)

        #@TODO: change from reloadAll event to package update event
        self.pyload.pullManager.add_event(Reload_all_event("collector"))


    #--------------------------------------------------------------------------

    @lock
    @change
    def add_package(self, name, folder, queue=0):
        """Adds a package, default to link collector"""
        lastID = self.db.add_package(name, folder, queue)
        p = self.db.get_package(lastID)
        e = InsertEvent("pack", lastID, p.order, "collector" if not queue else "queue")
        self.pyload.pullManager.add_event(e)
        return lastID


    #--------------------------------------------------------------------------

    @lock
    @change
    def delete_package(self, id):
        """Delete package and all contained links"""

        p = self.get_package(id)
        if not p:
            if id in self.packageCache:
                del self.packageCache[id]
            return

        oldorder = p.order
        queue = p.queue

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")

        pyfiles = self.cache.values()

        for pyfile in pyfiles:
            if pyfile.packageid == id:
                pyfile.abortDownload()
                pyfile.release()

        self.db.delete_package(p)
        self.pyload.pullManager.add_event(e)
        self.pyload.addonManager.dispatch_event("package-deleted", id)

        if id in self.packageCache:
            del self.packageCache[id]

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue == queue and pack.order > oldorder:
                pack.order -= 1
                pack.notifyChange()


    #--------------------------------------------------------------------------

    @lock
    @change
    def delete_link(self, id):
        """Deletes links"""

        f = self.get_file(id)
        if not f:
            return None

        pid = f.packageid
        e = RemoveEvent("file", id, "collector" if not f.package().queue else "queue")

        oldorder = f.order

        if id in self.pyload.threadManager.processing_ids():
            self.cache[id].abort_download()

        if id in self.cache:
            del self.cache[id]

        self.db.delete_link(f)

        self.pyload.pullManager.add_event(e)

        p = self.get_package(pid)
        if not len(p.getChildren()):
            p.delete()

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == pid and pyfile.order > oldorder:
                pyfile.order -= 1
                pyfile.notifyChange()


    #--------------------------------------------------------------------------

    def release_link(self, id):
        """Removes pyfile from cache"""
        if id in self.cache:
            del self.cache[id]


    #--------------------------------------------------------------------------

    def release_package(self, id):
        """Removes package from cache"""
        if id in self.packageCache:
            del self.packageCache[id]


    #--------------------------------------------------------------------------

    def update_link(self, pyfile):
        """Updates link"""
        self.db.update_link(pyfile)

        e = UpdateEvent("file", pyfile.id, "collector" if not pyfile.package().queue else "queue")
        self.pyload.pullManager.add_event(e)


    #--------------------------------------------------------------------------

    def update_package(self, pypack):
        """Updates a package"""
        self.db.update_package(pypack)

        e = UpdateEvent("pack", pypack.id, "collector" if not pypack.queue else "queue")
        self.pyload.pullManager.add_event(e)


    #--------------------------------------------------------------------------

    def get_package(self, id):
        """Return package instance"""

        if id in self.packageCache:
            return self.packageCache[id]
        else:
            return self.db.get_package(id)


    #--------------------------------------------------------------------------

    def get_package_data(self, id):
        """Returns dict with package information"""
        pack = self.get_package(id)

        if not pack:
            return None

        pack = pack.toDict()[id]

        data = self.db.get_package_data(id)

        tmplist = []

        cache = self.cache.values()
        for x in cache:
            if int(x.toDbDict()[x.id]['package']) == int(id):
                tmplist.append((x.id, x.toDbDict()[x.id]))
        data.update(tmplist)

        pack['links'] = data

        return pack


    #--------------------------------------------------------------------------

    def get_file_data(self, id):
        """Returns dict with file information"""
        if id in self.cache:
            return self.cache[id].to_db_dict()

        return self.db.get_link_data(id)


    #--------------------------------------------------------------------------

    def get_file(self, id):
        """Returns pyfile instance"""
        if id in self.cache:
            return self.cache[id]
        else:
            return self.db.get_file(id)


    #--------------------------------------------------------------------------

    @lock
    def get_job(self, occ):
        """Get suitable job"""

        #@TODO: clean mess
        #@TODO: improve selection of valid jobs

        if occ in self.jobCache:
            if self.jobCache[occ]:
                id = self.jobCache[occ].pop()
                if id == "empty":
                    pyfile = None
                    self.jobCache[occ].append("empty")
                else:
                    pyfile = self.get_file(id)
            else:
                jobs = self.db.get_job(occ)
                jobs.reverse()
                if not jobs:
                    self.jobCache[occ].append("empty")
                    pyfile = None
                else:
                    self.jobCache[occ].extend(jobs)
                    pyfile = self.get_file(self.jobCache[occ].pop())

        else:
            self.jobCache = {}  #: better not caching to much
            jobs = self.db.get_job(occ)
            jobs.reverse()
            self.jobCache[occ] = jobs

            if not jobs:
                self.jobCache[occ].append("empty")
                pyfile = None
            else:
                pyfile = self.get_file(self.jobCache[occ].pop())

            #@TODO: maybe the new job has to be approved...

        # pyfile = self.get_file(self.jobCache[occ].pop())
        return pyfile


    @lock
    def get_decrypt_job(self):
        """Return job for decrypting"""
        if "decrypt" in self.jobCache:
            return None

        plugins = self.pyload.pluginManager.crypterPlugins.keys() + self.pyload.pluginManager.containerPlugins.keys()
        plugins = str(tuple(plugins))

        jobs = self.db.get_plugin_job(plugins)
        if jobs:
            return self.get_file(jobs[0])
        else:
            self.jobCache['decrypt'] = "empty"
            return None


    def get_file_count(self):
        """Returns number of files"""

        if self.filecount == -1:
            self.filecount = self.db.filecount(1)

        return self.filecount


    def get_queue_count(self, force=False):
        """Number of files that have to be processed"""
        if self.queuecount == -1 or force:
            self.queuecount = self.db.queuecount(1)

        return self.queuecount


    def check_all_links_finished(self):
        """Checks if all files are finished and dispatch event"""

        if not self.get_queue_count(True):
            self.pyload.addonManager.dispatch_event("all_downloads-finished")
            self.pyload.log.debug("All downloads finished")
            return True

        return False


    def check_all_links_processed(self, fid):
        """Checks if all files was processed and pyload would idle now, needs fid which will be ignored when counting"""

        # reset count so statistic will update (this is called when dl was processed)
        self.reset_count()

        if not self.db.processcount(1, fid):
            self.pyload.addonManager.dispatch_event("all_downloads-processed")
            self.pyload.log.debug("All downloads processed")
            return True

        return False


    def reset_count(self):
        self.queuecount = -1


    @lock
    @change
    def restart_package(self, id):
        """Restart package"""
        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid == id:
                self.restart_file(pyfile.id)

        self.db.restart_package(id)

        if id in self.packageCache:
            self.packageCache[id].setFinished = False

        e = UpdateEvent("pack", id, "collector" if not self.get_package(id).queue else "queue")
        self.pyload.pullManager.add_event(e)


    @lock
    @change
    def restart_file(self, id):
        """Restart file"""
        if id in self.cache:
            self.cache[id].status = 3
            self.cache[id].name = self.cache[id].url
            self.cache[id].error = ""
            self.cache[id].abort_download()

        self.db.restart_file(id)

        e = UpdateEvent("file", id, "collector" if not self.get_file(id).package().queue else "queue")
        self.pyload.pullManager.add_event(e)


    @lock
    @change
    def set_package_location(self, id, queue):
        """Push package to queue"""

        p = self.db.get_package(id)
        oldorder = p.order

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.pullManager.add_event(e)

        self.db.clear_package_order(p)

        p = self.db.get_package(id)

        p.queue = queue
        self.db.update_package(p)

        self.db.reorder_package(p, -1, True)

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue != queue and pack.order > oldorder:
                pack.order -= 1
                pack.notifyChange()

        self.db.commit()
        self.release_package(id)
        p = self.get_package(id)

        e = InsertEvent("pack", id, p.order, "collector" if not p.queue else "queue")
        self.pyload.pullManager.add_event(e)


    @lock
    @change
    def reorder_package(self, id, position):
        p = self.get_package(id)

        e = RemoveEvent("pack", id, "collector" if not p.queue else "queue")
        self.pyload.pullManager.add_event(e)
        self.db.reorder_package(p, position)

        packs = self.packageCache.values()
        for pack in packs:
            if pack.queue != p.queue or pack.order < 0 or pack == p:
                continue
            if p.order > position:
                if position <= pack.order < p.order:
                    pack.order += 1
                    pack.notifyChange()
            elif p.order < position:
                if position >= pack.order > p.order:
                    pack.order -= 1
                    pack.notifyChange()

        p.order = position
        self.db.commit()

        e = InsertEvent("pack", id, position, "collector" if not p.queue else "queue")
        self.pyload.pullManager.add_event(e)


    @lock
    @change
    def reorder_file(self, id, position):
        f = self.get_file_data(id)
        f = f[id]

        e = RemoveEvent("file", id, "collector" if not self.get_package(f['package']).queue else "queue")
        self.pyload.pullManager.add_event(e)

        self.db.reorder_link(f, position)

        pyfiles = self.cache.values()
        for pyfile in pyfiles:
            if pyfile.packageid != f['package'] or pyfile.order < 0:
                continue
            if f['order'] > position:
                if position <= pyfile.order < f['order']:
                    pyfile.order += 1
                    pyfile.notifyChange()
            elif f['order'] < position:
                if position >= pyfile.order > f['order']:
                    pyfile.order -= 1
                    pyfile.notifyChange()

        if id in self.cache:
            self.cache[id].order = position

        self.db.commit()

        e = InsertEvent("file", id, position, "collector" if not self.get_package(f['package']).queue else "queue")
        self.pyload.pullManager.add_event(e)


    @change
    def update_file_info(self, data, pid):
        """Updates file info (name, size, status, url)"""
        ids = self.db.update_link_info(data)
        e = UpdateEvent("pack", pid, "collector" if not self.get_package(pid).queue else "queue")
        self.pyload.pullManager.add_event(e)


    def check_package_finished(self, pyfile):
        """Checks if package is finished and calls AddonManager"""

        ids = self.db.get_unfinished(pyfile.packageid)
        if not ids or (pyfile.id in ids and len(ids) == 1):
            if not pyfile.package().setFinished:
                self.pyload.log.info(_("Package finished: %s") % pyfile.package().name)
                self.pyload.addonManager.package_finished(pyfile.package())
                pyfile.package().setFinished = True


    def re_check_package(self, pid):
        """Recheck links in package"""
        data = self.db.get_package_data(pid)

        urls = []

        for pyfile in data.itervalues():
            if pyfile['status'] not in (0, 12, 13):
                urls.append((pyfile['url'], pyfile['plugin']))

        self.pyload.threadManager.create_info_thread(urls, pid)


    @lock
    @change
    def delete_finished_links(self):
        """Deletes finished links and packages, return deleted packages"""

        old_packs = self.get_info_data(0)
        old_packs.update(self.get_info_data(1))

        self.db.delete_finished()

        new_packs = self.db.get_all_packages(0)
        new_packs.update(self.db.get_all_packages(1))
        # get new packages only from db

        deleted = [id for id in old_packs.iterkeys() if id not in new_packs]
        for id_deleted in deleted:
            self.delete_package(int(id_deleted))

        return deleted


    @lock
    @change
    def restart_failed(self):
        """Restart all failed links"""
        self.db.restart_failed()


class File_methods(object):


    @style.queue
    def filecount(self, queue):
        """Returns number of files in queue"""
        self.c.execute("SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=?",
                       (queue,))
        return self.c.fetchone()[0]


    @style.queue
    def queuecount(self, queue):
        """Number of files in queue not finished yet"""
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status NOT IN (0, 4)",
            (queue,))
        return self.c.fetchone()[0]


    @style.queue
    def processcount(self, queue, fid):
        """Number of files which have to be proccessed"""
        self.c.execute(
            "SELECT COUNT(*) FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? AND l.status IN (2, 3, 5, 7, 12) AND l.id != ?",
            (queue, str(fid)))
        return self.c.fetchone()[0]


    @style.inner
    def _next_package_order(self, queue=0):
        self.c.execute('SELECT MAX(packageorder) FROM packages WHERE queue=?', (queue,))
        max = self.c.fetchone()[0]
        if max is not None:
            return max + 1
        else:
            return 0


    @style.inner
    def _next_file_order(self, package):
        self.c.execute('SELECT MAX(linkorder) FROM links WHERE package=?', (package,))
        max = self.c.fetchone()[0]
        if max is not None:
            return max + 1
        else:
            return 0


    @style.queue
    def add_link(self, url, name, plugin, package):
        order = self._next_file_order(package)
        self.c.execute('INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)',
                       (url, name, ".".join(plugintype, pluginname), package, order))
        return self.c.lastrowid


    @style.queue
    def add_links(self, links, package):
        """Links is a list of tupels (url, plugin)"""
        order = self._next_file_order(package)
        orders = [order + x for x in xrange(len(links))]
        links = [(x[0], x[0], ".".join((x[1], x[2])), package, o) for x, o in zip(links, orders)]
        self.c.executemany('INSERT INTO links(url, name, plugin, package, linkorder) VALUES(?,?,?,?,?)', links)


    @style.queue
    def add_package(self, name, folder, queue):
        order = self._next_package_order(queue)
        self.c.execute('INSERT INTO packages(name, folder, queue, packageorder) VALUES(?,?,?,?)',
                       (name, folder, queue, order))
        return self.c.lastrowid


    @style.queue
    def delete_package(self, p):
        self.c.execute('DELETE FROM links WHERE package=?', (str(p.id),))
        self.c.execute('DELETE FROM packages WHERE id=?', (str(p.id),))
        self.c.execute('UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=?',
                       (p.order, p.queue))


    @style.queue
    def delete_link(self, f):
        self.c.execute('DELETE FROM links WHERE id=?', (str(f.id),))
        self.c.execute('UPDATE links SET linkorder=linkorder-1 WHERE linkorder > ? AND package=?',
                       (f.order, str(f.packageid)))


    @style.queue
    def get_all_links(self, q):
        """
        Return information about all links in queue q

        q0 queue
        q1 collector

        format:

        {
            id: {'name': name, ... 'package': id }, ...
        }

        """
        self.c.execute(
            'SELECT l.id, l.url, l.name, l.size, l.status, l.error, l.plugin, l.package, l.linkorder FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE p.queue=? ORDER BY l.linkorder',
            (q,))
        data = {}
        for r in self.c:
            data[r[0]] = {
                'id': r[0],
                'url': r[1],
                'name': r[2],
                'size': r[3],
                'format_size': format_size(r[3]),
                'status': r[4],
                'statusmsg': self.manager.statusMsg[r[4]],
                'error': r[5],
                'plugin': tuple(r[6].split('.')),
                'package': r[7],
                'order': r[8],
            }

        return data


    @style.queue
    def get_all_packages(self, q):
        """
        Return information about packages in queue q
        (only useful in get all data)

        q0 queue
        q1 collector

        format:

        {
            id: {'name': name ... 'links': {}}, ...
        }
        """
        self.c.execute('SELECT p.id, p.name, p.folder, p.site, p.password, p.queue, p.packageorder, s.sizetotal, s.sizedone, s.linksdone, s.linkstotal \
            FROM packages p JOIN pstats s ON p.id = s.id \
            WHERE p.queue=? ORDER BY p.packageorder', str(q))

        data = {}
        for r in self.c:
            data[r[0]] = {
                'id': r[0],
                'name': r[1],
                'folder': r[2],
                'site': r[3],
                'password': r[4],
                'queue': r[5],
                'order': r[6],
                'sizetotal': int(r[7]),
                'sizedone': r[8] if r[8] else 0,  #: these can be None
                'linksdone': r[9] if r[9] else 0,
                'linkstotal': r[10],
                'links': {}
            }

        return data


    @style.queue
    def get_link_data(self, id):
        """Get link information as dict"""
        self.c.execute('SELECT id, url, name, size, status, error, plugin, package, linkorder FROM links WHERE id=?',
                       (str(id),))
        data = {}
        r = self.c.fetchone()
        if not r:
            return None
        data[r[0]] = {
            'id': r[0],
            'url': r[1],
            'name': r[2],
            'size': r[3],
            'format_size': format_size(r[3]),
            'status': r[4],
            'statusmsg': self.manager.statusMsg[r[4]],
            'error': r[5],
            'plugin': tuple(r[6].split('.')),
            'package': r[7],
            'order': r[8],
        }

        return data


    @style.queue
    def get_package_data(self, id):
        """Get data about links for a package"""
        self.c.execute(
            'SELECT id, url, name, size, status, error, plugin, package, linkorder FROM links WHERE package=? ORDER BY linkorder',
            (str(id),))

        data = {}
        for r in self.c:
            data[r[0]] = {
                'id': r[0],
                'url': r[1],
                'name': r[2],
                'size': r[3],
                'format_size': format_size(r[3]),
                'status': r[4],
                'statusmsg': self.manager.statusMsg[r[4]],
                'error': r[5],
                'plugin': tuple(r[6].split('.')),
                'package': r[7],
                'order': r[8],
            }

        return data


    @style.async
    def update_link(self, f):
        self.c.execute('UPDATE links SET url=?, name=?, size=?, status=?, error=?, package=? WHERE id=?',
                       (f.url, f.name, f.size, f.status, str(f.error), str(f.packageid), str(f.id)))


    @style.queue
    def update_package(self, p):
        self.c.execute('UPDATE packages SET name=?, folder=?, site=?, password=?, queue=? WHERE id=?',
                       (p.name, p.folder, p.site, p.password, p.queue, str(p.id)))

    @style.queue
    def update_link_info(self, data):
        """Data is list of tupels (name, size, status, url)"""
        self.c.executemany('UPDATE links SET name=?, size=?, status=? WHERE url=? AND status IN (1, 2, 3, 14)', data)
        ids = []
        self.c.execute('SELECT id FROM links WHERE url IN (\'%s\')' % "','".join([x[3] for x in data]))
        for r in self.c:
            ids.append(int(r[0]))
        return ids


    @style.queue
    def reorder_package(self, p, position, no_move=False):
        if position == -1:
            position = self._next_package_order(p.queue)
        if not noMove:
            if p.order > position:
                self.c.execute(
                    'UPDATE packages SET packageorder=packageorder+1 WHERE packageorder >= ? AND packageorder < ? AND queue=? AND packageorder >= 0',
                    (position, p.order, p.queue))
            elif p.order < position:
                self.c.execute(
                    'UPDATE packages SET packageorder=packageorder-1 WHERE packageorder <= ? AND packageorder > ? AND queue=? AND packageorder >= 0',
                    (position, p.order, p.queue))

        self.c.execute('UPDATE packages SET packageorder=? WHERE id=?', (position, str(p.id)))


    @style.queue
    def reorder_link(self, f, position):
        """Reorder link with f as dict for pyfile"""
        if f['order'] > position:
            self.c.execute('UPDATE links SET linkorder=linkorder+1 WHERE linkorder >= ? AND linkorder < ? AND package=?',
                           (position, f['order'], f['package']))
        elif f['order'] < position:
            self.c.execute('UPDATE links SET linkorder=linkorder-1 WHERE linkorder <= ? AND linkorder > ? AND package=?',
                           (position, f['order'], f['package']))

        self.c.execute('UPDATE links SET linkorder=? WHERE id=?', (position, f['id']))


    @style.queue
    def clear_package_order(self, p):
        self.c.execute('UPDATE packages SET packageorder=? WHERE id=?', (-1, str(p.id)))
        self.c.execute('UPDATE packages SET packageorder=packageorder-1 WHERE packageorder > ? AND queue=? AND id != ?',
                       (p.order, p.queue, str(p.id)))


    @style.async
    def restart_file(self, id):
        self.c.execute('UPDATE links SET status=3, error="" WHERE id=?', (str(id),))


    @style.async
    def restart_package(self, id):
        self.c.execute('UPDATE links SET status=3 WHERE package=?', (str(id),))


    @style.queue
    def get_package(self, id):
        """Return package instance from id"""
        self.c.execute("SELECT name, folder, site, password, queue, packageorder FROM packages WHERE id=?", (str(id),))
        r = self.c.fetchone()
        if not r:
            return None
        return PyPackage(self.manager, id, *r)


    #--------------------------------------------------------------------------

    @style.queue
    def get_file(self, id):
        """Return link instance from id"""
        self.c.execute("SELECT url, name, size, status, error, plugin, package, linkorder FROM links WHERE id=?",
                       (str(id),))
        r = self.c.fetchone()
        if not r:
            return None
        r = list(r)
        r[5] = tuple(r[5].split('.'))
        return PyFile(self.manager, id, *r)


    @style.queue
    def get_job(self, occ):
        """Return pyfile ids, which are suitable for download and dont use a occupied plugin"""

        #@TODO: improve this hardcoded method
        pre = "('CCF', 'DLC', 'LinkList', 'RSDF', 'TXT')"  #: plugins which are processed in collector

        cmd = "("
        for i, item in enumerate(occ):
            if i: cmd += ", "
            cmd += "'%s'" % item

        cmd += ")"

        cmd = "SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE ((p.queue=1 AND l.plugin NOT IN %s) OR l.plugin IN %s) AND l.status IN (2, 3, 14) ORDER BY p.packageorder ASC, l.linkorder ASC LIMIT 5" % (cmd, pre)

        self.c.execute(cmd)  #: very bad!

        return [x[0] for x in self.c]


    @style.queue
    def get_plugin_job(self, plugins):
        """Returns pyfile ids with suited plugins"""
        cmd = "SELECT l.id FROM links as l INNER JOIN packages as p ON l.package=p.id WHERE l.plugin IN %s AND l.status IN (2, 3, 14) ORDER BY p.packageorder ASC, l.linkorder ASC LIMIT 5" % plugins

        self.c.execute(cmd)  #: very bad!

        return [x[0] for x in self.c]


    @style.queue
    def get_unfinished(self, pid):
        """Return list of max length 3 ids with pyfiles in package not finished or processed"""

        self.c.execute("SELECT id FROM links WHERE package=? AND status NOT IN (0, 4, 13) LIMIT 3", (str(pid),))
        return [r[0] for r in self.c]


    @style.queue
    def delete_finished(self):
        self.c.execute("DELETE FROM links WHERE status IN (0, 4)")
        self.c.execute("DELETE FROM packages WHERE NOT EXISTS(SELECT 1 FROM links WHERE packages.id=links.package)")


    @style.queue
    def restart_failed(self):
        self.c.execute("UPDATE links SET status=3, error='' WHERE status IN (6, 8, 9)")


    @style.queue
    def find_duplicates(self, id, folder, filename):
        """Checks if filename exists with different id and same package"""
        self.c.execute(
            "SELECT l.plugin FROM links as l INNER JOIN packages as p ON l.package=p.id AND p.folder=? WHERE l.id!=? AND l.status=0 AND l.name=?",
            (folder, id, filename))
        return self.c.fetchone()


    @style.queue
    def purge_links(self):
        self.c.execute("DELETE FROM links;")
        self.c.execute("DELETE FROM packages;")


DatabaseBackend.registerSub(FileMethods)
