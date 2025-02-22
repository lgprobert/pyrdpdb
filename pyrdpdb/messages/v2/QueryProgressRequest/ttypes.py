#
# Autogenerated by Thrift Compiler (0.11.0)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
from thrift.TRecursive import fix_spec

import sys

from thrift.transport import TTransport
all_structs = []


class QueryProgressRequest(object):
    """
    Attributes:
     - queryId
     - queryKey
    """


    def __init__(self, queryId=None, queryKey=None,):
        self.queryId = queryId
        self.queryKey = queryKey

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I64:
                    self.queryId = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.queryKey = iprot.readI64()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('QueryProgressRequest')
        if self.queryId is not None:
            oprot.writeFieldBegin('queryId', TType.I64, 1)
            oprot.writeI64(self.queryId)
            oprot.writeFieldEnd()
        if self.queryKey is not None:
            oprot.writeFieldBegin('queryKey', TType.I64, 2)
            oprot.writeI64(self.queryKey)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.queryId is None:
            raise TProtocolException(message='Required field queryId is unset!')
        if self.queryKey is None:
            raise TProtocolException(message='Required field queryKey is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(QueryProgressRequest)
QueryProgressRequest.thrift_spec = (
    None,  # 0
    (1, TType.I64, 'queryId', None, None, ),  # 1
    (2, TType.I64, 'queryKey', None, None, ),  # 2
)
fix_spec(all_structs)
del all_structs
