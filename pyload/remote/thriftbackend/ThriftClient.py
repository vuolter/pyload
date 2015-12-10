# -*- coding: utf-8 -*-

import socket
import sys
import traceback

import thrift

from pyload.remote.thriftbackend.Protocol import Protocol
from pyload.remote.thriftbackend.Socket import Socket

# modules should import ttypes from here, when want to avoid importing API
from pyload.remote.thriftbackend.thriftgen.pyload import Pyload
from pyload.remote.thriftbackend.thriftgen.pyload.ttypes import *


ConnectionClosed = thrift.transport.TTransport.TTransportException


class Wrong_login(Exception):
    pass


class No_connection(Exception):
    pass


class NoSSL(Exception):
    pass


class Thrift_client(object):

    def __init__(self, host="localhost", port=7227, user="", password=""):

        self.create_connection(host, port)
        try:
            self.transport.open()

        except socket.error, e:
            if e.args and e.args[0] in (111, 10061):
                raise NoConnection
            else:
                traceback.print_exc()
                raise NoConnection

        try:
            correct = self.client.login(user, password)

        except socket.error, e:
            if e.args and e.args[0] == 104:
                # connection reset by peer, probably wants ssl
                try:
                    self.create_connection(host, port, True)
                    # set timeout or a ssl socket will block when querying none ssl server
                    self.socket.set_timeout(10)

                except ImportError:
                    #@TODO untested
                    raise NoSSL
                try:
                   self.transport.open()
                   correct = self.client.login(user, password)
                finally:
                    self.socket.set_timeout(None)
            elif e.args and e.args[0] == 32:
                raise NoConnection
            else:
                traceback.print_exc()
                raise NoConnection

        if not correct:
            self.transport.close()
            raise WrongLogin


    def create_connection(self, host, port, ssl=False):
        self.socket = Socket(host, port, ssl)
        self.transport = thrift.transport.TTransport.TBuffered_transport(self.socket)
        # self.transport = thrift.transport.TZlibTransport.TZlib_transport(thrift.transport.TTransport.TBuffered_transport(self.socket))

        protocol = Protocol(self.transport)
        self.client = Pyload.Client(protocol)


    def close(self):
        self.transport.close()


    def __getattr__(self, item):
        return getattr(self.client, item)
