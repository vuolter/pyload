# -*- coding: utf-8 -*-

import SocketServer

from pyload.manager.Remote import BackendBase


class Request_handler(Socket_server.Base_request_handler):

    def setup(self):
        pass


    def handle(self):
        print self.request.recv(1024)


class Socket_backend(Backend_base):

    def setup(self, host, port):
        # local only
        self.server = SocketServer.ThreadingTCPServer(("localhost", port), RequestHandler)


    def serve(self):
        self.server.serve_forever()
