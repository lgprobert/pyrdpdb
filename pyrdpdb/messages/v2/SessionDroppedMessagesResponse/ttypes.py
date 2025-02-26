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


class DroppedMessageInfo(object):
    """
    Attributes:
     - messageSize
     - messageType
    """


    def __init__(self, messageSize=None, messageType=None,):
        self.messageSize = messageSize
        self.messageType = messageType

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
                    self.messageSize = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.messageType = iprot.readI32()
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
        oprot.writeStructBegin('DroppedMessageInfo')
        if self.messageSize is not None:
            oprot.writeFieldBegin('messageSize', TType.I32, 1)
            oprot.writeI32(self.messageSize)
            oprot.writeFieldEnd()
        if self.messageType is not None:
            oprot.writeFieldBegin('messageType', TType.I32, 2)
            oprot.writeI32(self.messageType)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.messageSize is None:
            raise TProtocolException(message='Required field messageSize is unset!')
        if self.messageType is None:
            raise TProtocolException(message='Required field messageType is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class SessionDroppedMessagesResponse(object):
    """
    Attributes:
     - droppedMessages
     - missingDroppedMessages
    """


    def __init__(self, droppedMessages=None, missingDroppedMessages=None,):
        self.droppedMessages = droppedMessages
        self.missingDroppedMessages = missingDroppedMessages

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
                    self.droppedMessages = []
                    (_etype3, _size0) = iprot.readListBegin()
                    for _i4 in range(_size0):
                        _elem5 = DroppedMessageInfo()
                        _elem5.read(iprot)
                        self.droppedMessages.append(_elem5)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.BOOL:
                    self.missingDroppedMessages = iprot.readBool()
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
        oprot.writeStructBegin('SessionDroppedMessagesResponse')
        if self.droppedMessages is not None:
            oprot.writeFieldBegin('droppedMessages', TType.LIST, 1)
            oprot.writeListBegin(TType.STRUCT, len(self.droppedMessages))
            for iter6 in self.droppedMessages:
                iter6.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.missingDroppedMessages is not None:
            oprot.writeFieldBegin('missingDroppedMessages', TType.BOOL, 2)
            oprot.writeBool(self.missingDroppedMessages)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.missingDroppedMessages is None:
            raise TProtocolException(message='Required field missingDroppedMessages is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(DroppedMessageInfo)
DroppedMessageInfo.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'messageSize', None, None, ),  # 1
    (2, TType.I32, 'messageType', None, None, ),  # 2
)
all_structs.append(SessionDroppedMessagesResponse)
SessionDroppedMessagesResponse.thrift_spec = (
    None,  # 0
    (1, TType.LIST, 'droppedMessages', (TType.STRUCT, [DroppedMessageInfo, None], False), None, ),  # 1
    (2, TType.BOOL, 'missingDroppedMessages', None, None, ),  # 2
)
fix_spec(all_structs)
del all_structs
