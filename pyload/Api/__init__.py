# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import with_statement

import base64
import os
import re
import time
import urlparse

from pyload.Datatype import PyFile
from pyload.misc import decode
from pyload.misc.packagetools import parse_names
from pyload.network.RequestFactory import getURL
from pyload.remote import activated
from pyload.misc import compare_time, free_space, safe_filename

if activated:
    try:
        import thrift

        from pyload.remote.thriftbackend.thriftgen.pyload.ttypes import *
        from pyload.remote.thriftbackend.thriftgen.pyload.Pyload import Iface

        BaseObject = thrift.protocol.TBase

    except ImportError:
        from pyload.Api.types import *
        print "Thrift not imported"

else:
    from pyload.Api.types import *

# contains function names mapped to their permissions
# unlisted functions are for admins only
permMap = {}


# decorator only called on init, never initialized, so has no effect on runtime
def permission(bits):
    class __dec(object):

        def __new__(cls, func, *args, **kwargs):
            permMap[func.__name__] = bits
            return func
    return _Dec


urlmatcher = re.compile(r"((https?|ftps?|xdcc|sftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&\[\]\|]*)", re.IGNORECASE)


class PERMS(object):
    ALL = 0  #: requires no permission, but login
    ADD = 1  #: can add packages
    DELETE = 2  #: can delete packages
    STATUS = 4  #: see and change server status
    LIST = 16  #: see queue and collector
    MODIFY = 32  #: moddify some attribute of downloads
    DOWNLOAD = 64  #: can download from webinterface
    SETTINGS = 128  #: can access settings
    ACCOUNTS = 256  #: can access accounts
    LOGS = 512  #: can see server logs


class ROLE(object):
    ADMIN = 0  #: admin has all permissions implicit
    USER = 1


def has_permission(userperms, perms):
    # bytewise or perms before if needed
    return perms == (userperms & perms)


class Api(Iface):
    """
    **pyLoads API**

    This is accessible either internal via pyload.api or via thrift backend.

    see Thrift specification file remote/thriftbackend/pyload.thrift\
    for information about data structures and what methods are usuable with rpc.

    Most methods requires specific permissions, please look at the source code if you need to know.\
    These can be configured via webinterface.
    Admin user have all permissions, and are the only ones who can access the methods with no specific permission.
    """
    EXTERNAL = Iface  #: let the json api know which methods are external


    def __init__(self, core):
        self.pyload = core


    def _convert_py_file(self, p):
        fdata = FileData(p['id'], p['url'], p['name'], p['plugin'], p['size'],
                         p['format_size'], p['status'], p['statusmsg'],
                         p['package'], p['error'], p['order'])
        return fdata


    def _convert_config_format(self, c):
        sections = {}
        for sectionName, sub in c.iteritems():
            section = ConfigSection(sectionName, sub['desc'])
            items = []
            for key, data in sub.iteritems():
                if key in ("desc", "outline"):
                    continue
                item = ConfigItem()
                item.name = key
                item.description = data['desc']
                item.value = str(data['value']) if not isinstance(data['value'], basestring) else data['value']
                item.type = data['type']
                items.append(item)
            section.items = items
            sections[sectionName] = section
            if "outline" in sub:
                section.outline = sub['outline']
        return sections


    @permission(PERMS.SETTINGS)
    def get_config_value(self, category, option, section="core"):
        """
        Retrieve config value.

        :param category: name of category, or plugin
        :param option: config option
        :param section: 'plugin' or 'core'
        :return: config value as string
        """
        if section == "core":
            value = self.pyload.config[category][option]
        else:
            value = self.pyload.config.get_plugin(category, option)
        return str(value)


    @permission(PERMS.SETTINGS)
    def set_config_value(self, category, option, value, section="core"):
        """
        Set new config value.

        :param section:
        :param option:
        :param value: new config value
        :param section: 'plugin' or 'core
        """
        self.pyload.addonManager.dispatch_event("config-changed", category, option, value, section)
        if section == "core":
            self.pyload.config[category][option] = value
            if option in ("limit_speed", "max_speed"):  #: not so nice to update the limit
                self.pyload.requestFactory.update_bucket()
        elif section == "plugin":
            self.pyload.config.set_plugin(category, option, value)


    @permission(PERMS.SETTINGS)
    def get_config(self):
        """
        Retrieves complete config of core.

        :return: list of `ConfigSection`
        """
        return self._convert_config_format(self.pyload.config.config)


    def get_config_dict(self):
        """
        Retrieves complete config in dict format, not for RPC.

        :return: dict
        """
        return self.pyload.config.config


    @permission(PERMS.SETTINGS)
    def get_plugin_config(self):
        """
        Retrieves complete config for all plugins.

        :return: list of `ConfigSection`
        """
        return self._convert_config_format(self.pyload.config.plugin)


    def get_plugin_config_dict(self):
        """
        Plugin config as dict, not for RPC.

        :return: dict
        """
        return self.pyload.config.plugin


    @permission(PERMS.STATUS)
    def pause_server(self):
        """
        Pause server: Tt wont start any new downloads, but nothing gets aborted."""
        self.pyload.threadManager.pause = True


    @permission(PERMS.STATUS)
    def unpause_server(self):
        """
        Unpause server: New Downloads will be started."""
        self.pyload.threadManager.pause = False


    @permission(PERMS.STATUS)
    def toggle_pause(self):
        """
        Toggle pause state.

        :return: new pause state
        """
        self.pyload.threadManager.pause ^= True
        return self.pyload.threadManager.pause


    @permission(PERMS.STATUS)
    def toggle_reconnect(self):
        """
        Toggle reconnect activation.

        :return: new reconnect state
        """
        self.pyload.config['reconnect']['activated'] ^= True
        return self.pyload.config.get("reconnect", "activated")


    @permission(PERMS.LIST)
    def status_server(self):
        """
        Some general information about the current status of pyLoad.

        :return: `ServerStatus`
        """
        serverStatus = ServerStatus(self.pyload.threadManager.pause, len(self.pyload.threadManager.processing_ids()),
                                    self.pyload.files.get_queue_count(), self.pyload.files.get_file_count(), 0,
                                    not self.pyload.threadManager.pause and self.is_time_download(),
                                    self.pyload.config.get("reconnect", "activated") and self.is_time_reconnect())
        for pyfile in [x.active for x in self.pyload.threadManager.threads if x.active and isinstance(x.active, PyFile)]:
            serverStatus.speed += pyfile.get_speed()  #: bytes/s
        return serverStatus


    @permission(PERMS.STATUS)
    def free_space(self):
        """
        Available free space at download directory in bytes"""
        return free_space(self.pyload.config.get("general", "download_folder"))


    @permission(PERMS.ALL)
    def get_server_version(self):
        """
        pyLoad Core version"""
        return self.pyload.version


    def kill(self):
        """
        Clean way to quit pyLoad"""
        self.pyload.do_kill = True


    def restart(self):
        """
        Restart pyload core"""
        self.pyload.do_restart = True


    @permission(PERMS.LOGS)
    def get_log(self, offset=0):
        """
        Returns most recent log entries.

        :param offset: line offset
        :return: List of log entries
        """
        filename = os.path.join(self.pyload.config.get("log", "log_folder"), 'log.txt')
        try:
            with open(filename, "r") as fh:
                lines = fh.readlines()
            if offset >= len(lines):
                return []
            return lines[offset:]
        except Exception:
            return ['No log available']


    @permission(PERMS.STATUS)
    def is_time_download(self):
        """
        Checks if pyload will start new downloads according to time in config.

        :return: bool
        """
        start = self.pyload.config.get("downloadTime", "start").split(":")
        end = self.pyload.config.get("downloadTime", "end").split(":")
        return compare_time(start, end)


    @permission(PERMS.STATUS)
    def is_time_reconnect(self):
        """
        Checks if pyload will try to make a reconnect

        :return: bool
        """
        start = self.pyload.config.get("reconnect", "start").split(":")
        end = self.pyload.config.get("reconnect", "end").split(":")
        return compare_time(start, end) and self.pyload.config.get("reconnect", "activated")


    @permission(PERMS.LIST)
    def status_downloads(self):
        """
        Status off all currently running downloads.

        :return: list of `DownloadStatus`
        """
        data = []
        for pyfile in self.pyload.threadManager.get_active_files():
            if not isinstance(pyfile, PyFile):
                continue
            data.append(DownloadInfo(
                pyfile.id, pyfile.name, pyfile.get_speed(), pyfile.getETA(), pyfile.formatETA(),
                pyfile.get_bytes_left(), pyfile.get_size(), pyfile.format_size(), pyfile.get_percent(),
                pyfile.status, pyfile.get_status_name(), pyfile.format_wait(),
                pyfile.waitUntil, pyfile.packageid, pyfile.package().name, pyfile.pluginname))
        return data


    @permission(PERMS.ADD)
    def add_package(self, name, links, dest=Destination.Queue):
        """
        Adds a package, with links to desired destination.

        :param name: name of the new package
        :param links: list of urls
        :param dest: `Destination`
        :return: package id of the new package
        """
        if self.pyload.config.get("general", "folder_per_package"):
            folder = urlparse.urlparse(name).path.split("/")[-1]
        else:
            folder = ""

        folder = safe_filename(folder)

        pid = self.pyload.files.add_package(name, folder, dest)

        self.pyload.files.add_links(links, pid)

        self.pyload.log.info(_("Added package %(name)s containing %(count)d links") % {"name": decode(name), "count": len(links)})

        self.pyload.files.save()

        return pid


    @permission(PERMS.ADD)
    def parse_URLs(self, html=None, url=None):
        """
        Parses html content or any arbitaty text for links and returns result of `check_URLs`

        :param html: html source
        :return:
        """
        urls = []
        if html:
            urls += [x[0] for x in urlmatcher.findall(html)]
        if url:
            page = getURL(url)
            urls += [x[0] for x in urlmatcher.findall(page)]
        # remove duplicates
        return self.check_URLs(set(urls))


    @permission(PERMS.ADD)
    def check_URLs(self, urls):
        """
        Gets urls and returns pluginname mapped to list of matches urls.

        :param urls:
        :return: {plugin: urls}
        """
        data = self.pyload.pluginManager.parse_urls(urls)
        plugins = {}

        for url, plugintype, pluginname in data:
            try:
                plugins[plugintype][pluginname].append(url)
            except Exception:
                plugins[plugintype][pluginname] = [url]

        return plugins


    @permission(PERMS.ADD)
    def check_online_status(self, urls):
        """
        Initiates online status check

        :param urls:
        :return: initial set of data as `OnlineCheck` instance containing the result id
        """
        data = self.pyload.pluginManager.parse_urls(urls)

        rid = self.pyload.threadManager.create_result_thread(data, False)

        tmp = [(url, (url, OnlineStatus(url, (plugintype, pluginname), "unknown", 3, 0))) for url, plugintype, pluginname in data]
        data = parse_names(tmp)
        result = {}
        for k, v in data.iteritems():
            for url, status in v:
                status.packagename = k
                result[url] = status

        return OnlineCheck(rid, result)


    @permission(PERMS.ADD)
    def check_online_status_container(self, urls, container, data):
        """
        Checks online status of urls and a submited container file

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: online check
        """
        with open(os.path.join(self.pyload.config.get("general", "download_folder"), "tmp_" + container), "wb") as th:
            th.write(str(data))
        return self.check_online_status(urls + [th.name])


    @permission(PERMS.ADD)
    def poll_results(self, rid):
        """
        Polls the result available for ResultID

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then no more data available
        """
        result = self.pyload.threadManager.get_info_result(rid)
        if "ALL_INFO_FETCHED" in result:
            del result['ALL_INFO_FETCHED']
            return OnlineCheck(-1, result)
        else:
            return OnlineCheck(rid, result)


    @permission(PERMS.ADD)
    def generate_packages(self, links):
        """
        Parses links, generates packages names from urls

        :param links: list of urls
        :return: package names mapped to urls
        """
        return parse_names((x, x) for x in links)


    @permission(PERMS.ADD)
    def generate_and_add_packages(self, links, dest=Destination.Queue):
        """
        Generates and add packages

        :param links: list of urls
        :param dest: `Destination`
        :return: list of package ids
        """
        return [self.add_package(name, urls, dest) for name, urls
                in self.generate_packages(links).iteritems()]


    @permission(PERMS.ADD)
    def check_and_add_packages(self, links, dest=Destination.Queue):
        """
        Checks online status, retrieves names, and will add packages.\
        Because of this packages are not added immediatly, only for internal use.

        :param links: list of urls
        :param dest: `Destination`
        :return: None
        """
        data = self.pyload.pluginManager.parse_urls(links)
        self.pyload.threadManager.create_result_thread(data, True)


    @permission(PERMS.LIST)
    def get_package_data(self, pid):
        """
        Returns complete information about package, and included files.

        :param pid: package id
        :return: `PackageData` with .links attribute
        """
        data = self.pyload.files.get_package_data(int(pid))
        if not data:
            raise PackageDoesNotExists(pid)
        return PackageData(data['id'], data['name'], data['folder'], data['site'], data['password'],
                           data['queue'], data['order'],
                           links=[self._convert_py_file(x) for x in data['links'].itervalues()])


    @permission(PERMS.LIST)
    def get_package_info(self, pid):
        """
        Returns information about package, without detailed information about containing files

        :param pid: package id
        :return: `PackageData` with .fid attribute
        """
        data = self.pyload.files.get_package_data(int(pid))

        if not data:
            raise PackageDoesNotExists(pid)
        return PackageData(data['id'], data['name'], data['folder'], data['site'], data['password'],
                           data['queue'], data['order'],
                           fids=[int(x) for x in data['links']])


    @permission(PERMS.LIST)
    def get_file_data(self, fid):
        """
        Get complete information about a specific file.

        :param fid: file id
        :return: `FileData`
        """
        info = self.pyload.files.get_file_data(int(fid))
        if not info:
            raise FileDoesNotExists(fid)
        return self._convert_py_file(info.values()[0])


    @permission(PERMS.DELETE)
    def delete_files(self, fids):
        """
        Deletes several file entries from pyload.

        :param fids: list of file ids
        """
        for fid in fids:
            self.pyload.files.delete_link(int(fid))
        self.pyload.files.save()


    @permission(PERMS.DELETE)
    def delete_packages(self, pids):
        """
        Deletes packages and containing links.

        :param pids: list of package ids
        """
        for pid in pids:
            self.pyload.files.delete_package(int(pid))
        self.pyload.files.save()


    @permission(PERMS.LIST)
    def get_queue(self):
        """
        Returns info about queue and packages, **not** about files, see `getQueueData` \
        or `getPackageData` instead.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack['id'], pack['name'], pack['folder'], pack['site'],
                            pack['password'], pack['queue'], pack['order'],
                            pack['linksdone'], pack['sizedone'], pack['sizetotal'],
                            pack['linkstotal'])
                for pack in self.pyload.files.get_info_data(Destination.Queue).itervalues()]


    @permission(PERMS.LIST)
    def get_queue_data(self):
        """
        Return complete data about everything in queue, this is very expensive use it sparely.\
           See `getQueue` for alternative.

        :return: list of `PackageData`
        """
        return [PackageData(pack['id'], pack['name'], pack['folder'], pack['site'],
                            pack['password'], pack['queue'], pack['order'],
                            pack['linksdone'], pack['sizedone'], pack['sizetotal'],
                            links=[self._convert_py_file(x) for x in pack['links'].itervalues()])
                for pack in self.pyload.files.get_complete_data(Destination.Queue).itervalues()]


    @permission(PERMS.LIST)
    def get_collector(self):
        """
        Same as `getQueue` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack['id'], pack['name'], pack['folder'], pack['site'],
                            pack['password'], pack['queue'], pack['order'],
                            pack['linksdone'], pack['sizedone'], pack['sizetotal'],
                            pack['linkstotal'])
                for pack in self.pyload.files.get_info_data(Destination.Collector).itervalues()]


    @permission(PERMS.LIST)
    def get_collector_data(self):
        """
        Same as `getQueueData` for collector.

        :return: list of `PackageInfo`
        """
        return [PackageData(pack['id'], pack['name'], pack['folder'], pack['site'],
                            pack['password'], pack['queue'], pack['order'],
                            pack['linksdone'], pack['sizedone'], pack['sizetotal'],
                            links=[self._convert_py_file(x) for x in pack['links'].itervalues()])
                for pack in self.pyload.files.get_complete_data(Destination.Collector).itervalues()]


    @permission(PERMS.ADD)
    def add_files(self, pid, links):
        """
        Adds files to specific package.

        :param pid: package id
        :param links: list of urls
        """
        self.pyload.files.add_links(links, int(pid))
        self.pyload.log.info(_("Added %(count)d links to package #%(package)d ") % {"count": len(links), "package": pid})
        self.pyload.files.save()


    @permission(PERMS.MODIFY)
    def push_to_queue(self, pid):
        """
        Moves package from Collector to Queue.

        :param pid: package id
        """
        self.pyload.files.set_package_location(pid, Destination.Queue)


    @permission(PERMS.MODIFY)
    def pull_from_queue(self, pid):
        """
        Moves package from Queue to Collector.

        :param pid: package id
        """
        self.pyload.files.set_package_location(pid, Destination.Collector)


    @permission(PERMS.MODIFY)
    def restart_package(self, pid):
        """
        Restarts a package, resets every containing files.

        :param pid: package id
        """
        self.pyload.files.restart_package(int(pid))


    @permission(PERMS.MODIFY)
    def restart_file(self, fid):
        """
        Resets file status, so it will be downloaded again.

        :param fid:  file id
        """
        self.pyload.files.restart_file(int(fid))


    @permission(PERMS.MODIFY)
    def recheck_package(self, pid):
        """
        Proofes online status of all files in a package, also a default action when package is added.

        :param pid:
        :return:
        """
        self.pyload.files.re_check_package(int(pid))


    @permission(PERMS.MODIFY)
    def stop_all_downloads(self):
        """
        Aborts all running downloads."""

        pyfiles = self.pyload.files.cache.values()
        for pyfile in pyfiles:
            pyfile.abort_download()


    @permission(PERMS.MODIFY)
    def stop_downloads(self, fids):
        """
        Aborts specific downloads.

        :param fids: list of file ids
        :return:
        """
        pyfiles = self.pyload.files.cache.values()
        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abort_download()


    @permission(PERMS.MODIFY)
    def set_package_name(self, pid, name):
        """
        Renames a package.

        :param pid: package id
        :param name: new package name
        """
        pack = self.pyload.files.get_package(pid)
        pack.name = name
        pack.sync()


    @permission(PERMS.MODIFY)
    def move_package(self, destination, pid):
        """
        Set a new package location.

        :param destination: `Destination`
        :param pid: package id
        """
        if destination in (0, 1):
            self.pyload.files.set_package_location(pid, destination)


    @permission(PERMS.MODIFY)
    def move_files(self, fids, pid):
        """
        Move multiple files to another package

        :param fids: list of file ids
        :param pid: destination package
        :return:
        """
        # TODO: implement
        pass


    @permission(PERMS.ADD)
    def upload_container(self, filename, data):
        """
        Uploads and adds a container file to pyLoad.

        :param filename: filename, extension is important so it can correctly decrypted
        :param data: file content
        """
        with open(os.path.join(self.pyload.config.get("general", "download_folder"), "tmp_" + filename), "wb") as th:
            th.write(str(data))
        self.add_package(th.name, [th.name], Destination.Queue)


    @permission(PERMS.MODIFY)
    def order_package(self, pid, position):
        """
        Gives a package a new position.

        :param pid: package id
        :param position:
        """
        self.pyload.files.reorder_package(pid, position)


    @permission(PERMS.MODIFY)
    def order_file(self, fid, position):
        """
        Gives a new position to a file within its package.

        :param fid: file id
        :param position:
        """
        self.pyload.files.reorder_file(fid, position)


    @permission(PERMS.MODIFY)
    def set_package_data(self, pid, data):
        """
        Allows to modify several package attributes.

        :param pid: package id
        :param data: dict that maps attribute to desired value
        """
        package = self.pyload.files.get_package(pid)
        if not package:
            raise PackageDoesNotExists(pid)
        for key, value in data.iteritems():
            if key == "id":
                continue
            setattr(package, key, value)
        package.sync()
        self.pyload.files.save()


    @permission(PERMS.DELETE)
    def delete_finished(self):
        """
        Deletes all finished files and completly finished packages.

        :return: list of deleted package ids
        """
        return self.pyload.files.delete_finished_links()


    @permission(PERMS.MODIFY)
    def restart_failed(self):
        """
        Restarts all failed failes."""
        self.pyload.files.restart_failed()


    @permission(PERMS.LIST)
    def get_package_order(self, destination):
        """
        Returns information about package order.

        :param destination: `Destination`
        :return: dict mapping order to package id
        """
        packs = self.pyload.files.get_info_data(destination)
        order = {}
        for pid in packs:
            pack = self.pyload.files.get_package_data(int(pid))
            while pack['order'] in order.keys():  #: just in case
                pack['order'] += 1
            order[pack['order']] = pack['id']
        return order


    @permission(PERMS.LIST)
    def get_file_order(self, pid):
        """
        Information about file order within package.

        :param pid:
        :return: dict mapping order to file id
        """
        rawdata = self.pyload.files.get_package_data(int(pid))
        order = {}
        for id, pyfile in rawdata['links'].iteritems():
            while pyfile['order'] in order.keys():  #: just in case
                pyfile['order'] += 1
            order[pyfile['order']] = pyfile['id']
        return order


    @permission(PERMS.STATUS)
    def is_captcha_waiting(self):
        """
        Indicates wether a captcha task is available

        :return: bool
        """
        self.pyload.lastClientConnected = time.time()
        task = self.pyload.captchaManager.get_task()
        return not task is None


    @permission(PERMS.STATUS)
    def get_captcha_task(self, exclusive=False):
        """
        Returns a captcha task

        :param exclusive: unused
        :return: `CaptchaTask`
        """
        self.pyload.lastClientConnected = time.time()
        task = self.pyload.captchaManager.get_task()
        if task:
            task.setWatingForUser(exclusive=exclusive)
            data, type, result = task.getCaptcha()
            ctask = CaptchaTask(int(task.id), base64.standard_b64encode(data), type, result)
            return ctask
        return CaptchaTask(-1)


    @permission(PERMS.STATUS)
    def get_captcha_task_status(self, tid):
        """
        Get information about captcha task

        :param tid: task id
        :return: string
        """
        self.pyload.lastClientConnected = time.time()
        task = self.pyload.captchaManager.getTaskByID(tid)
        return task.getStatus() if task else ""


    @permission(PERMS.STATUS)
    def set_captcha_result(self, tid, result):
        """
        Set result for a captcha task

        :param tid: task id
        :param result: captcha result
        """
        self.pyload.lastClientConnected = time.time()
        task = self.pyload.captchaManager.getTaskByID(tid)
        if task:
            task.setResult(result)
            self.pyload.captchaManager.remove_task(task)


    @permission(PERMS.STATUS)
    def get_events(self, uuid):
        """
        Lists occured events, may be affected to changes in future.

        :param uuid:
        :return: list of `Events`
        """
        events = self.pyload.pullManager.get_events(uuid)
        new_events = []


        def conv_dest(d):
            return Destination.Queue if d == "queue" else Destination.Collector

        for e in events:
            event = EventInfo()
            event.eventname = e[0]
            if e[0] in ("update", "remove", "insert"):
                event.id = e[3]
                event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                event.destination = convDest(e[1])
            elif e[0] == "order":
                if e[1]:
                    event.id = e[1]
                    event.type = ElementType.Package if e[2] == "pack" else ElementType.File
                    event.destination = convDest(e[3])
            elif e[0] == "reload":
                event.destination = convDest(e[1])
            new_events.append(event)
        return new_events


    @permission(PERMS.ACCOUNTS)
    def get_accounts(self, refresh):
        """
        Get information about all entered accounts.

        :param refresh: reload account info
        :return: list of `AccountInfo`
        """
        accs = self.pyload.accountManager.get_account_infos(False, refresh)
        for group in accs.values():
            accounts = [AccountInfo(acc['validuntil'], acc['login'], acc['options'], acc['valid'],
                                    acc['trafficleft'], acc['maxtraffic'], acc['premium'], acc['type'])
                        for acc in group]
        return accounts or list()


    @permission(PERMS.ALL)
    def get_account_types(self):
        """
        All available account types.

        :return: list
        """
        return self.pyload.accountManager.accounts.keys()


    @permission(PERMS.ACCOUNTS)
    def update_account(self, plugin, account, password=None, options={}):
        """
        Changes pw/options for specific account."""
        self.pyload.accountManager.update_account(plugin, account, password, options)


    @permission(PERMS.ACCOUNTS)
    def remove_account(self, plugin, account):
        """
        Remove account from pyload.

        :param plugin: pluginname
        :param account: accountname
        """
        self.pyload.accountManager.remove_account(plugin, account)


    @permission(PERMS.ALL)
    def login(self, username, password, remoteip=None):
        """
        Login into pyLoad, this **must** be called when using rpc before any methods can be used.

        :param username:
        :param password:
        :param remoteip: Omit this argument, its only used internal
        :return: bool indicating login was successful
        """
        return bool(self.check_auth(username, password, remoteip))


    def check_auth(self, username, password):
        """
        Check authentication and returns details

        :param username:
        :param password:
        :param remoteip:
        :return: dict with info, empty when login is incorrect
        """
        return self.pyload.db.check_auth(username, password) or None


    def is_authorized(self, func, userdata):
        """
        Checks if the user is authorized for specific method

        :param func: function name
        :param userdata: dictionary of user data
        :return: boolean
        """
        if userdata == "local" or userdata['role'] == ROLE.ADMIN:
            return True
        elif func in permMap and has_permission(userdata['permission'], permMap[func]):
            return True
        else:
            return False


    @permission(PERMS.ALL)
    def get_user_data(self, username, password):
        """
        Similar to `checkAuth` but returns UserData thrift type"""
        user = self.check_auth(username, password)
        if user:
            return UserData(user['name'], user['email'], user['role'], user['permission'], user['template'])
        else:
            return UserData()


    def get_all_user_data(self):
        """
        Returns all known user and info"""
        return dict((user, UserData(user, data['email'], data['role'], data['permission'], data['template'])) for user, data
                in self.pyload.db.get_all_user_data().iteritems())


    @permission(PERMS.STATUS)
    def get_services(self):
        """
        A dict of available services, these can be defined by addon plugins.

        :return: dict with this style: {"plugin": {"method": "description"}}
        """
        return dict((plugin, funcs) for plugin, funcs in self.pyload.addonManager.methods.iteritems())


    @permission(PERMS.STATUS)
    def has_service(self, plugin, func):
        """
        Checks wether a service is available.

        :param plugin:
        :param func:
        :return: bool
        """
        cont = self.pyload.addonManager.methods
        return plugin in cont and func in cont[plugin]


    @permission(PERMS.STATUS)
    def call(self, info):
        """
        Calls a service (a method in addon plugin).

        :param info: `ServiceCall`
        :return: result
        :raises: ServiceDoesNotExists, when its not available
        :raises: ServiceException, when a exception was raised
        """
        plugin = info.plugin
        func = info.func
        args = info.arguments
        parse = info.parseArguments
        if not self.has_service(plugin, func):
            raise ServiceDoesNotExists(plugin, func)
        try:
            ret = self.pyload.addonManager.callRPC(plugin, func, args, parse)
        except Exception, e:
            raise ServiceException(e.message)


    @permission(PERMS.STATUS)
    def get_all_info(self):
        """
        Returns all information stored by addon plugins. Values are always strings

        :return: {"plugin": {"name": value}}
        """
        return self.pyload.addonManager.get_all_info()


    @permission(PERMS.STATUS)
    def get_info_by_plugin(self, plugin):
        """
        Returns information stored by a specific plugin.

        :param plugin: pluginname
        :return: dict of attr names mapped to value {"name": value}
        """
        return self.pyload.addonManager.get_info(plugin)


    def change_password(self, user, oldpw, newpw):
        """
        Changes password for specific user"""
        return self.pyload.db.change_password(user, oldpw, newpw)


    def set_user_permission(self, user, perm, role):
        self.pyload.db.set_permission(user, perm)
        self.pyload.db.set_role(user, role)
