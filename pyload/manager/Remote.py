# -*- coding: utf-8 -*-
# @author: RaNaN

import threading
import traceback


class Backend_base(threading.Thread):

    def __init__(self, manager):
        threading.Thread.__init__(self)
        self.manager = manager
        self.pyload = manager.core
        self.enabled = True
        self.running = False


    def run(self):
        self.running = True
        try:
            self.serve()
        except Exception, e:
            self.pyload.log.error(_("Remote backend error: %s") % e)
            if self.pyload.debug:
                traceback.print_exc()
        finally:
            self.running = False


    def setup(self, host, port):
        pass


    def check_deps(self):
        return True


    def serve(self):
        pass


    def shutdown(self):
        pass


    def stop(self):
        self.enabled = False  #: set flag and call shutdowm message, so thread can react
        self.shutdown()


class Remote_manager(object):
    available = []


    def __init__(self, core):
        self.pyload = core
        self.backends = []

        if self.pyload.remote:
            self.available.append("ThriftBackend")
        # else:
            # self.available.append("SocketBackend")


    def start_backends(self):
        host = self.pyload.config.get("remote", "listenaddr")
        port = self.pyload.config.get("remote", "port")

        for b in self.available:
            klass = getattr(__import__("pyload.remote.%s" % b, globals(), locals(), [b], -1), b)
            backend = klass(self)
            if not backend.checkDeps():
                continue
            try:
                backend.setup(host, port)
                self.pyload.log.info(_("Starting %(name)s: %(addr)s:%(port)s") % {"name": b, "addr": host, "port": port})
            except Exception, e:
                self.pyload.log.error(_("Failed loading backend %(name)s | %(error)s") % {"name": b, "error": str(e)})
                if self.pyload.debug:
                    traceback.print_exc()
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
