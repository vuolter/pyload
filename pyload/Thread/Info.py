# -*- coding: utf-8 -*-
# @author: RaNaN

import Queue
import os
import sys
import time
import traceback

from pyload.Api import OnlineStatus
from pyload.Datatype import PyFile
from pyload.Thread.Plugin import PluginThread
from pyload.plugin.Hoster import parseFileInfo


class Info_thread(Plugin_thread):

    def __init__(self, manager, data, pid=-1, rid=-1, add=False):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.data = data
        self.pid = pid  #: package id
        # [ .. (name, plugin) .. ]

        self.rid = rid  #: result id
        self.add = add  #: add packages instead of return result

        self.cache = []  #: accumulated data

        self.start()


    def run(self):
        """Run method"""

        plugins = {}
        container = []

        for url, plugintype, pluginname in self.data:
            # filter out container plugins
            if plugintype == 'container':
                container.appen((pluginname, url))
            else:
                if (plugintype, pluginname) in plugins:
                    plugins[(plugintype, pluginname)].append(url)
                else:
                    plugins[(plugintype, pluginname)] = [url]

        # directly write to database
        if self.pid > -1:
            for (plugintype, pluginname), urls in plugins.iteritems():
                plugin = self.pyload.pluginManager.plugin_class(plugintype, pluginname)
                if hasattr(plugin, "getInfo"):
                    self.fetch_for_plugin(pluginname, plugin, urls, self.updateDB)
                    self.pyload.files.save()

        elif self.add:
            for (plugintype, pluginname), urls in plugins.iteritems():
                plugin = self.pyload.pluginManager.plugin_class(plugintype, pluginname)
                if hasattr(plugin, "getInfo"):
                    self.fetch_for_plugin(pluginname, plugin, urls, self.updateCache, True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.update_cache(pluginname, result)

            packs = parseNames([(name, url) for name, x, y, url in self.cache])

            self.pyload.log.debug("Fetched and generated %d packages" % len(packs))

            for k, v in packs:
                self.pyload.api.add_package(k, v)

            # empty cache
            del self.cache[:]

        else:  #: post the results

            for name, url in container:
                # attach container content
                try:
                    data = self.decrypt_container(name, url)
                except Exception:
                    self.pyload.log.error("Could not decrypt container.")
                    if self.pyload.debug:
                        traceback.print_exc()
                    data = []

                for url, plugintype, pluginname in data:
                    try:
                        plugins[plugintype][pluginname].append(url)
                    except Exception:
                        plugins[plugintype][pluginname] = [url]

            self.manager.infoResults[self.rid] = {}

            for plugintype, pluginname, urls in plugins.iteritems():
                plugin = self.pyload.pluginManager.plugin_class(plugintype, pluginname)
                if hasattr(plugin, "getInfo"):
                    self.fetch_for_plugin(pluginname, plugin, urls, self.updateResult, True)

                    # force to process cache
                    if self.cache:
                        self.update_result(pluginname, [], True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.update_result(pluginname, result, True)

            self.manager.infoResults[self.rid]['ALL_INFO_FETCHED'] = {}

        self.manager.timestamp = time.time() + 5 * 60


    def updateDB(self, plugin, result):
        self.pyload.files.update_file_info(result, self.pid)


    def update_result(self, plugin, result, force=False):
        # parse package name and generate result
        # accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            # used for package generating
            tmp = [(name, (url, OnlineStatus(name, plugin, "unknown", status, int(size)))) for name, size, status, url in self.cache]

            data = parseNames(tmp)
            result = {}
            for k, v in data.iteritems():
                for url, status in v:
                    status.packagename = k
                    result[url] = status

            self.manager.set_info_results(self.rid, result)

            self.cache = []


    def update_cache(self, plugin, result):
        self.cache.extend(result)


    def fetch_for_plugin(self, pluginname, plugin, urls, cb, err=None):
        try:
            result = []  #: result loaded from cache
            process = []  #: urls to process
            for url in urls:
                if url in self.manager.infoCache:
                    result.append(self.manager.infoCache[url])
                else:
                    process.append(url)

            if result:
                self.pyload.log.debug("Fetched %d values from cache for %s" % (len(result), pluginname))
                cb(pluginname, result)

            if process:
                self.pyload.log.debug("Run Info Fetching for %s" % pluginname)
                for url in process:
                    if hasattr(plugin, "URL_REPLACEMENTS"):
                        url = replace_patterns(url, plugin.URL_REPLACEMENTS)

                    result = parseFileInfo(plugin, url)

                    if not type(result) == list:
                        result = [result]

                    for res in result:
                        self.manager.infoCache[res[3]] = res  # : why don't assign res dict directly?

                    cb(pluginname, result)

            self.pyload.log.debug("Finished Info Fetching for %s" % pluginname)
        except Exception, e:
            self.pyload.log.warning(_("Info Fetching for %(name)s failed | %(err)s") % {"name": pluginname, "err": str(e)})
            if self.pyload.debug:
                traceback.print_exc()

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)


    def decrypt_container(self, plugin, url):
        data = []
        # only works on container plugins

        self.pyload.log.debug("Pre decrypting %s with %s" % (url, plugin))

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, url, url, 0, 0, "", plugin, -1, -1)

        pyfile.initPlugin()

        # little plugin lifecycle
        try:
            pyfile.plugin.setup()
            pyfile.plugin.loadToDisk()
            pyfile.plugin.decrypt(pyfile)
            pyfile.plugin.deleteTmp()

            for pack in pyfile.plugin.packages:
                pyfile.plugin.urls.extend(pack[1])

            data = self.pyload.pluginManager.parse_urls(pyfile.plugin.urls)

            self.pyload.log.debug("Got %d links." % len(data))

        except Exception, e:
            self.pyload.log.debug("Pre decrypting error: %s" % str(e))
        finally:
            pyfile.release()

        return data
