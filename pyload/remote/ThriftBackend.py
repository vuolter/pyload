# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay

import os

import thrift

from pyload.manager.Remote import BackendBase
from pyload.remote.thriftbackend.Processor import Processor
from pyload.remote.thriftbackend.Protocol import ProtocolFactory
from pyload.remote.thriftbackend.Socket import ServerSocket
from pyload.remote.thriftbackend.Transport import TransportFactory
# from pyload.remote.thriftbackend.Transport import TransportFactoryCompressed


class Thrift_backend(Backend_base):

    def setup(self, host, port):
        processor = Processor(self.pyload.api)

        key = None
        cert = None

        if self.pyload.config.get("ssl", "activated"):
            if os.path.exists(self.pyload.config.get("ssl", "cert")) and os.path.exists(self.pyload.config.get("ssl", "key")):
                self.pyload.log.info(_("Using SSL ThriftBackend"))
                key = self.pyload.config.get("ssl", "key")
                cert = self.pyload.config.get("ssl", "cert")

        transport = ServerSocket(port, host, key, cert)


        # tfactory = TransportFactoryCompressed()
        tfactory = TransportFactory()
        pfactory = ProtocolFactory()

        self.server = thrift.server.TServer.TThreadedServer(processor, transport, tfactory, pfactory)
        # self.server = TNonblockingServer.TNonblockingServer(processor, transport, tfactory, pfactory)

        # server = thrift.server.TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)


    def serve(self):
        self.server.serve()
