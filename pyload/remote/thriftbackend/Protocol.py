# -*- coding: utf-8 -*-

import thrift

from pyload.misc import decode, encode


class Protocol(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocol):

    def write_string(self, str):
        str = encode(str)
        self.write_i32(len(str))
        self.trans.write(str)


    def read_string(self):
        len = self.read_i32()
        str = self.trans.read_all(len)
        return decode(str)


class ProtocolFactory(thrift.protocol.TBinaryProtocol.thrift.protocol.TBinaryProtocolFactory):

    def get_protocol(self, trans):
        prot = Protocol(trans, self.strictRead, self.strictWrite)
        return prot
