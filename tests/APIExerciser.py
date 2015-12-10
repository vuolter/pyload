#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

import gc
import math
import random
import string
import threading
import time
import traceback

from pyload.remote.thriftbackend.ThriftClient import ThriftClient, Destination


def create_URLs():
    """Create some urls, some may fail"""
    urls = []
    for x in xrange(0, random.randint(20, 100)):
        name = "DEBUG_API"
        if random.randint(0, 5) == 5:
            name = ""  #: this link will fail

        urls.append(name + "".join(random.sample(string.ascii_letters, random.randint(10, 20))))

    return urls


AVOID = (0, 3, 8)

idPool = 0
sumCalled = 0


def start_api_exerciser(core, n):
    for _i in xrange(n):
        APIExerciser(core).start()


class APIExerciser(threading.Thread):

    def __init__(self, core, thrift=False, user=None, pw=None):
        global idPool

        threading.Thread.__init__(self)
        self.set_daemon(True)
        self.pyload = core
        self.count = 0  #: number of methods
        self.time = time.time()

        self.api = Thrift_client(user=user, password=pw) if thrift else pyload.api

        self.id = idPool

        idPool += 1

        # self.start()


    def run(self):

        self.pyload.log.info("API Excerciser started %d" % self.id)

        with open("error.log", "ab") as out:
            # core errors are not logged of course
            out.write("\n" + "Starting\n")
            out.flush()

            while True:
                try:
                    self.testAPI()
                except Exception:
                    self.pyload.log.error("Excerciser %d throw an execption" % self.id)
                    traceback.print_exc()
                    out.write(traceback.format_exc() + 2 * "\n")
                    out.flush()

                if not self.count % 100:
                    self.pyload.log.info("Exerciser %d tested %d api calls" % (self.id, self.count))
                if not self.count % 1000:
                    out.flush()

                if not sumCalled % 1000:  #: not thread safe
                    self.pyload.log.info("Exercisers tested %d api calls" % sumCalled)
                    persec = sumCalled / (time.time() - self.time)
                    self.pyload.log.info("Approx. %.2f calls per second." % persec)
                    self.pyload.log.info("Approx. %.2f ms per call." % (1000 / persec))
                    self.pyload.log.info("Collected garbage: %d" % gc.collect())
                    # time.sleep(random() / 500)


    def testAPI(self):
        global sumCalled

        m = ["statusDownloads", "statusServer", "addPackage", "getPackageData", "getFileData", "deleteFiles",
             "deletePackages", "getQueue", "getCollector", "getQueueData", "getCollectorData", "isCaptchaWaiting",
             "getCaptchaTask", "stopAllDownloads", "getAllInfo", "getServices", "getAccounts", "getAllUserData"]

        method = random.choice(m)
        # print "Testing:", method

        if hasattr(self, method):
            res = getattr(self, method)()
        else:
            res = getattr(self.api, method)()

        self.count += 1
        sumCalled += 1

        # print res


    def add_package(self):
        name = "".join(random.sample(string.ascii_letters, 10))
        urls = createURLs()

        self.api.add_package(name, urls, random.choice([Destination.Queue.Queue, Destination.Collector]))


    def delete_files(self):
        info = self.api.get_queue_data()
        if not info:
            return

        pack = random.choice(info)
        fids = pack.links

        if len(fids):
            fids = [f.fid for f in random.sample(fids, random.randint(1, max(len(fids) / 2, 1)))]
            self.api.delete_files(fids)


    def delete_packages(self):
        info = random.choice([self.api.get_queue(), self.api.get_collector()])
        if not info:
            return

        pids = [p.pid for p in info]
        if pids:
            pids = random.sample(pids, random.randint(1, max(math.floor(len(pids) / 2.5), 1)))
            self.api.delete_packages(pids)


    def get_file_data(self):
        info = self.api.get_queue_data()
        if info:
            p = random.choice(info)
            if p.links:
                self.api.get_file_data(random.choice(p.links).fid)


    def get_package_data(self):
        info = self.api.get_queue()
        if info:
            self.api.get_package_data(random.choice(info).pid)


    def get_accounts(self):
        self.api.get_accounts(False)


    def get_captcha_task(self):
        self.api.get_captcha_task(False)
