# -*- coding: utf-8 -*-

import thrift

from pyload.utils import decode, encode


class Protocol(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocol):

    def writeString(self, str):
        str = encode(str)
        self.writeI32(len(str))
        self.trans.write(str)


    def readString(self):
        len = self.readI32()
        str = self.trans.readAll(len)
        return decode(str)


class ProtocolFactory(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocolFactory):

    def getProtocol(self, trans):
        prot = Protocol(trans, self.strictRead, self.strictWrite)
        return prot
