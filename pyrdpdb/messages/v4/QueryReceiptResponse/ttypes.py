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


class StatementReceipt(object):
    """
    Attributes:
     - statementString
     - statementId
     - statementKey
    """


    def __init__(self, statementString=None, statementId=None, statementKey=None,):
        self.statementString = statementString
        self.statementId = statementId
        self.statementKey = statementKey

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
                if ftype == TType.STRING:
                    self.statementString = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.statementId = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.statementKey = iprot.readI64()
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
        oprot.writeStructBegin('StatementReceipt')
        if self.statementString is not None:
            oprot.writeFieldBegin('statementString', TType.STRING, 1)
            oprot.writeString(self.statementString.encode('utf-8') if sys.version_info[0] == 2 else self.statementString)
            oprot.writeFieldEnd()
        if self.statementId is not None:
            oprot.writeFieldBegin('statementId', TType.STRING, 2)
            oprot.writeString(self.statementId.encode('utf-8') if sys.version_info[0] == 2 else self.statementId)
            oprot.writeFieldEnd()
        if self.statementKey is not None:
            oprot.writeFieldBegin('statementKey', TType.I64, 3)
            oprot.writeI64(self.statementKey)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.statementId is None:
            raise TProtocolException(message='Required field statementId is unset!')
        if self.statementKey is None:
            raise TProtocolException(message='Required field statementKey is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class QueryReceiptResponse(object):
    """
    Attributes:
     - statementReceipts
    """


    def __init__(self, statementReceipts=None,):
        self.statementReceipts = statementReceipts

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
                if ftype == TType.LIST:
                    self.statementReceipts = []
                    (_etype3, _size0) = iprot.readListBegin()
                    for _i4 in range(_size0):
                        _elem5 = StatementReceipt()
                        _elem5.read(iprot)
                        self.statementReceipts.append(_elem5)
                    iprot.readListEnd()
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
        oprot.writeStructBegin('QueryReceiptResponse')
        if self.statementReceipts is not None:
            oprot.writeFieldBegin('statementReceipts', TType.LIST, 1)
            oprot.writeListBegin(TType.STRUCT, len(self.statementReceipts))
            for iter6 in self.statementReceipts:
                iter6.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.statementReceipts is None:
            raise TProtocolException(message='Required field statementReceipts is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(StatementReceipt)
StatementReceipt.thrift_spec = (
    None,  # 0
    (1, TType.STRING, 'statementString', 'UTF8', None, ),  # 1
    (2, TType.STRING, 'statementId', 'UTF8', None, ),  # 2
    (3, TType.I64, 'statementKey', None, None, ),  # 3
)
all_structs.append(QueryReceiptResponse)
QueryReceiptResponse.thrift_spec = (
    None,  # 0
    (1, TType.LIST, 'statementReceipts', (TType.STRUCT, [StatementReceipt, None], False), None, ),  # 1
)
fix_spec(all_structs)
del all_structs
