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


class ErrorResponse(object):
    """
    Attributes:
     - errorCode
     - sqlStateCode
     - errorString
     - stackTrace
    """


    def __init__(self, errorCode=None, sqlStateCode=None, errorString=None, stackTrace=None,):
        self.errorCode = errorCode
        self.sqlStateCode = sqlStateCode
        self.errorString = errorString
        self.stackTrace = stackTrace

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
                if ftype == TType.I32:
                    self.errorCode = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.sqlStateCode = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.errorString = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.stackTrace = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
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
        oprot.writeStructBegin('ErrorResponse')
        if self.errorCode is not None:
            oprot.writeFieldBegin('errorCode', TType.I32, 1)
            oprot.writeI32(self.errorCode)
            oprot.writeFieldEnd()
        if self.sqlStateCode is not None:
            oprot.writeFieldBegin('sqlStateCode', TType.STRING, 2)
            oprot.writeString(self.sqlStateCode.encode('utf-8') if sys.version_info[0] == 2 else self.sqlStateCode)
            oprot.writeFieldEnd()
        if self.errorString is not None:
            oprot.writeFieldBegin('errorString', TType.STRING, 3)
            oprot.writeString(self.errorString.encode('utf-8') if sys.version_info[0] == 2 else self.errorString)
            oprot.writeFieldEnd()
        if self.stackTrace is not None:
            oprot.writeFieldBegin('stackTrace', TType.STRING, 4)
            oprot.writeString(self.stackTrace.encode('utf-8') if sys.version_info[0] == 2 else self.stackTrace)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.errorString is None:
            raise TProtocolException(message='Required field errorString is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(ErrorResponse)
ErrorResponse.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'errorCode', None, None, ),  # 1
    (2, TType.STRING, 'sqlStateCode', 'UTF8', None, ),  # 2
    (3, TType.STRING, 'errorString', 'UTF8', None, ),  # 3
    (4, TType.STRING, 'stackTrace', 'UTF8', None, ),  # 4
)
fix_spec(all_structs)
del all_structs
