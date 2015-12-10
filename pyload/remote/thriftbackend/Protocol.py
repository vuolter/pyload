# -*- coding: utf-8 -*-

import thrift

from pyload.utils import decode, encode


class Protocol(thrift.protocol.TBinary_protocol.thrift.protocol.TBinary_protocol):

    def write_string(self, str):
        str = encode(str)
        self.write_i32(len(str))
        self.trans.write(str)


    def read_string(self):
        len = self.read_i32()
        str = self.trans.read_all(len)
        return decode(str)


class Protocol_factory(thrift.protocol.TBinary_protocol.thrift.protocol.TBinary_protocol_factory):

    def get_protocol(self, trans):
        prot = Protocol(trans, self.strictRead, self.strictWrite)
        return prot
