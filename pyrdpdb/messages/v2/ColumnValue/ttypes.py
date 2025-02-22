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


class IntervalType(object):
    YEAR_MONTH = 0
    DAY_TIME = 1

    _VALUES_TO_NAMES = {
        0: "YEAR_MONTH",
        1: "DAY_TIME",
    }

    _NAMES_TO_VALUES = {
        "YEAR_MONTH": 0,
        "DAY_TIME": 1,
    }


class Timestamp(object):
    """
    Attributes:
     - year
     - month
     - day
     - hour
     - minute
     - second
     - nanoseconds
    """


    def __init__(self, year=None, month=None, day=None, hour=None, minute=None, second=None, nanoseconds=None,):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.nanoseconds = nanoseconds

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
                    self.year = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I16:
                    self.month = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I16:
                    self.day = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I16:
                    self.hour = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.I16:
                    self.minute = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I16:
                    self.second = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.I32:
                    self.nanoseconds = iprot.readI32()
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
        oprot.writeStructBegin('Timestamp')
        if self.year is not None:
            oprot.writeFieldBegin('year', TType.I32, 1)
            oprot.writeI32(self.year)
            oprot.writeFieldEnd()
        if self.month is not None:
            oprot.writeFieldBegin('month', TType.I16, 2)
            oprot.writeI16(self.month)
            oprot.writeFieldEnd()
        if self.day is not None:
            oprot.writeFieldBegin('day', TType.I16, 3)
            oprot.writeI16(self.day)
            oprot.writeFieldEnd()
        if self.hour is not None:
            oprot.writeFieldBegin('hour', TType.I16, 4)
            oprot.writeI16(self.hour)
            oprot.writeFieldEnd()
        if self.minute is not None:
            oprot.writeFieldBegin('minute', TType.I16, 5)
            oprot.writeI16(self.minute)
            oprot.writeFieldEnd()
        if self.second is not None:
            oprot.writeFieldBegin('second', TType.I16, 6)
            oprot.writeI16(self.second)
            oprot.writeFieldEnd()
        if self.nanoseconds is not None:
            oprot.writeFieldBegin('nanoseconds', TType.I32, 7)
            oprot.writeI32(self.nanoseconds)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.year is None:
            raise TProtocolException(message='Required field year is unset!')
        if self.month is None:
            raise TProtocolException(message='Required field month is unset!')
        if self.day is None:
            raise TProtocolException(message='Required field day is unset!')
        if self.hour is None:
            raise TProtocolException(message='Required field hour is unset!')
        if self.minute is None:
            raise TProtocolException(message='Required field minute is unset!')
        if self.second is None:
            raise TProtocolException(message='Required field second is unset!')
        if self.nanoseconds is None:
            raise TProtocolException(message='Required field nanoseconds is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class Interval(object):
    """
    Attributes:
     - type
     - year
     - month
     - day
     - hour
     - minute
     - second
     - nanoseconds
    """


    def __init__(self, type=None, year=None, month=None, day=None, hour=None, minute=None, second=None, nanoseconds=None,):
        self.type = type
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.nanoseconds = nanoseconds

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
                    self.type = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I64:
                    self.year = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I64:
                    self.month = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I64:
                    self.day = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.I64:
                    self.hour = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I64:
                    self.minute = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.I64:
                    self.second = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.I64:
                    self.nanoseconds = iprot.readI64()
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
        oprot.writeStructBegin('Interval')
        if self.type is not None:
            oprot.writeFieldBegin('type', TType.I32, 1)
            oprot.writeI32(self.type)
            oprot.writeFieldEnd()
        if self.year is not None:
            oprot.writeFieldBegin('year', TType.I64, 2)
            oprot.writeI64(self.year)
            oprot.writeFieldEnd()
        if self.month is not None:
            oprot.writeFieldBegin('month', TType.I64, 3)
            oprot.writeI64(self.month)
            oprot.writeFieldEnd()
        if self.day is not None:
            oprot.writeFieldBegin('day', TType.I64, 4)
            oprot.writeI64(self.day)
            oprot.writeFieldEnd()
        if self.hour is not None:
            oprot.writeFieldBegin('hour', TType.I64, 5)
            oprot.writeI64(self.hour)
            oprot.writeFieldEnd()
        if self.minute is not None:
            oprot.writeFieldBegin('minute', TType.I64, 6)
            oprot.writeI64(self.minute)
            oprot.writeFieldEnd()
        if self.second is not None:
            oprot.writeFieldBegin('second', TType.I64, 7)
            oprot.writeI64(self.second)
            oprot.writeFieldEnd()
        if self.nanoseconds is not None:
            oprot.writeFieldBegin('nanoseconds', TType.I64, 8)
            oprot.writeI64(self.nanoseconds)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.type is None:
            raise TProtocolException(message='Required field type is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class ColumnValue(object):
    """
    Attributes:
     - isNull
     - booleanVal
     - tinyIntVal
     - smallIntVal
     - integerVal
     - bigintVal
     - doubleVal
     - bigDecimalVal
     - timestampVal
     - intervalVal
     - stringVal
     - binaryVal
    """


    def __init__(self, isNull=None, booleanVal=None, tinyIntVal=None, smallIntVal=None, integerVal=None, bigintVal=None, doubleVal=None, bigDecimalVal=None, timestampVal=None, intervalVal=None, stringVal=None, binaryVal=None,):
        self.isNull = isNull
        self.booleanVal = booleanVal
        self.tinyIntVal = tinyIntVal
        self.smallIntVal = smallIntVal
        self.integerVal = integerVal
        self.bigintVal = bigintVal
        self.doubleVal = doubleVal
        self.bigDecimalVal = bigDecimalVal
        self.timestampVal = timestampVal
        self.intervalVal = intervalVal
        self.stringVal = stringVal
        self.binaryVal = binaryVal

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
                if ftype == TType.BOOL:
                    self.isNull = iprot.readBool()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.BOOL:
                    self.booleanVal = iprot.readBool()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I16:
                    self.tinyIntVal = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.I16:
                    self.smallIntVal = iprot.readI16()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.I32:
                    self.integerVal = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.I64:
                    self.bigintVal = iprot.readI64()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.DOUBLE:
                    self.doubleVal = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.STRING:
                    self.bigDecimalVal = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.STRUCT:
                    self.timestampVal = Timestamp()
                    self.timestampVal.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 12:
                if ftype == TType.STRUCT:
                    self.intervalVal = Interval()
                    self.intervalVal.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 13:
                if ftype == TType.STRING:
                    self.stringVal = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 14:
                if ftype == TType.STRING:
                    self.binaryVal = iprot.readBinary()
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
        oprot.writeStructBegin('ColumnValue')
        if self.isNull is not None:
            oprot.writeFieldBegin('isNull', TType.BOOL, 1)
            oprot.writeBool(self.isNull)
            oprot.writeFieldEnd()
        if self.booleanVal is not None:
            oprot.writeFieldBegin('booleanVal', TType.BOOL, 2)
            oprot.writeBool(self.booleanVal)
            oprot.writeFieldEnd()
        if self.tinyIntVal is not None:
            oprot.writeFieldBegin('tinyIntVal', TType.I16, 3)
            oprot.writeI16(self.tinyIntVal)
            oprot.writeFieldEnd()
        if self.smallIntVal is not None:
            oprot.writeFieldBegin('smallIntVal', TType.I16, 4)
            oprot.writeI16(self.smallIntVal)
            oprot.writeFieldEnd()
        if self.integerVal is not None:
            oprot.writeFieldBegin('integerVal', TType.I32, 5)
            oprot.writeI32(self.integerVal)
            oprot.writeFieldEnd()
        if self.bigintVal is not None:
            oprot.writeFieldBegin('bigintVal', TType.I64, 6)
            oprot.writeI64(self.bigintVal)
            oprot.writeFieldEnd()
        if self.doubleVal is not None:
            oprot.writeFieldBegin('doubleVal', TType.DOUBLE, 7)
            oprot.writeDouble(self.doubleVal)
            oprot.writeFieldEnd()
        if self.bigDecimalVal is not None:
            oprot.writeFieldBegin('bigDecimalVal', TType.STRING, 8)
            oprot.writeString(self.bigDecimalVal.encode('utf-8') if sys.version_info[0] == 2 else self.bigDecimalVal)
            oprot.writeFieldEnd()
        if self.timestampVal is not None:
            oprot.writeFieldBegin('timestampVal', TType.STRUCT, 9)
            self.timestampVal.write(oprot)
            oprot.writeFieldEnd()
        if self.intervalVal is not None:
            oprot.writeFieldBegin('intervalVal', TType.STRUCT, 12)
            self.intervalVal.write(oprot)
            oprot.writeFieldEnd()
        if self.stringVal is not None:
            oprot.writeFieldBegin('stringVal', TType.STRING, 13)
            oprot.writeString(self.stringVal.encode('utf-8') if sys.version_info[0] == 2 else self.stringVal)
            oprot.writeFieldEnd()
        if self.binaryVal is not None:
            oprot.writeFieldBegin('binaryVal', TType.STRING, 14)
            oprot.writeBinary(self.binaryVal)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(Timestamp)
Timestamp.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'year', None, None, ),  # 1
    (2, TType.I16, 'month', None, None, ),  # 2
    (3, TType.I16, 'day', None, None, ),  # 3
    (4, TType.I16, 'hour', None, None, ),  # 4
    (5, TType.I16, 'minute', None, None, ),  # 5
    (6, TType.I16, 'second', None, None, ),  # 6
    (7, TType.I32, 'nanoseconds', None, None, ),  # 7
)
all_structs.append(Interval)
Interval.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'type', None, None, ),  # 1
    (2, TType.I64, 'year', None, None, ),  # 2
    (3, TType.I64, 'month', None, None, ),  # 3
    (4, TType.I64, 'day', None, None, ),  # 4
    (5, TType.I64, 'hour', None, None, ),  # 5
    (6, TType.I64, 'minute', None, None, ),  # 6
    (7, TType.I64, 'second', None, None, ),  # 7
    (8, TType.I64, 'nanoseconds', None, None, ),  # 8
)
all_structs.append(ColumnValue)
ColumnValue.thrift_spec = (
    None,  # 0
    (1, TType.BOOL, 'isNull', None, None, ),  # 1
    (2, TType.BOOL, 'booleanVal', None, None, ),  # 2
    (3, TType.I16, 'tinyIntVal', None, None, ),  # 3
    (4, TType.I16, 'smallIntVal', None, None, ),  # 4
    (5, TType.I32, 'integerVal', None, None, ),  # 5
    (6, TType.I64, 'bigintVal', None, None, ),  # 6
    (7, TType.DOUBLE, 'doubleVal', None, None, ),  # 7
    (8, TType.STRING, 'bigDecimalVal', 'UTF8', None, ),  # 8
    (9, TType.STRUCT, 'timestampVal', [Timestamp, None], None, ),  # 9
    None,  # 10
    None,  # 11
    (12, TType.STRUCT, 'intervalVal', [Interval, None], None, ),  # 12
    (13, TType.STRING, 'stringVal', 'UTF8', None, ),  # 13
    (14, TType.STRING, 'binaryVal', 'BINARY', None, ),  # 14
)
fix_spec(all_structs)
del all_structs
