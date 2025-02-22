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


class MessageTypes(object):
    ProtocolCompatibleRequest = 1
    ProtocolCompatibleResponse = 2
    ProtocolIncompatibleResponse = 4
    ErrorResponse = 6
    WarningResponse = 8
    ShutdownNotification = 10
    DisconnectNotification = 12
    DisconnectRequest = 13
    ClearTextTunnelRequest = 21
    TunnelSupportedResponse = 22
    PlainAuthenticationRequest = 31
    KerberosAuthenticationRequest = 33
    GssNegotiationMsg = 34
    AuthenticationOkResponse = 38
    SessionChangeRequest = 41
    SessionChangeResponse = 42
    QueryExecuteRequest = 51
    QueryReceiptResponse = 52
    RowMetadataResponse = 54
    RowDataResponse = 56
    StatementResponse = 58
    QueryExecuteResponse = 60
    QueryCancellationRequest = 71
    QueryCancellationResponse = 72
    QueryProgressRequest = 81
    QueryProgressResponse = 82
    SessionMonitoringRequest = 91
    SessionProtocolVersionResponse = 92
    SessionDataResponse = 94
    SessionDroppedMessagesResponse = 96
    SessionMonitoringResponse = 98
    ParseStatementRequest = 101
    ParseStatementResponse = 102
    StatementBindAndExecuteRequest = 103
    ClosePreparedStatementRequest = 105
    ClosePreparedStatementResponse = 106

    _VALUES_TO_NAMES = {
        1: "ProtocolCompatibleRequest",
        2: "ProtocolCompatibleResponse",
        4: "ProtocolIncompatibleResponse",
        6: "ErrorResponse",
        8: "WarningResponse",
        10: "ShutdownNotification",
        12: "DisconnectNotification",
        13: "DisconnectRequest",
        21: "ClearTextTunnelRequest",
        22: "TunnelSupportedResponse",
        31: "PlainAuthenticationRequest",
        33: "KerberosAuthenticationRequest",
        34: "GssNegotiationMsg",
        38: "AuthenticationOkResponse",
        41: "SessionChangeRequest",
        42: "SessionChangeResponse",
        51: "QueryExecuteRequest",
        52: "QueryReceiptResponse",
        54: "RowMetadataResponse",
        56: "RowDataResponse",
        58: "StatementResponse",
        60: "QueryExecuteResponse",
        71: "QueryCancellationRequest",
        72: "QueryCancellationResponse",
        81: "QueryProgressRequest",
        82: "QueryProgressResponse",
        91: "SessionMonitoringRequest",
        92: "SessionProtocolVersionResponse",
        94: "SessionDataResponse",
        96: "SessionDroppedMessagesResponse",
        98: "SessionMonitoringResponse",
        101: "ParseStatementRequest",
        102: "ParseStatementResponse",
        103: "StatementBindAndExecuteRequest",
        105: "ClosePreparedStatementRequest",
        106: "ClosePreparedStatementResponse",
    }

    _NAMES_TO_VALUES = {
        "ProtocolCompatibleRequest": 1,
        "ProtocolCompatibleResponse": 2,
        "ProtocolIncompatibleResponse": 4,
        "ErrorResponse": 6,
        "WarningResponse": 8,
        "ShutdownNotification": 10,
        "DisconnectNotification": 12,
        "DisconnectRequest": 13,
        "ClearTextTunnelRequest": 21,
        "TunnelSupportedResponse": 22,
        "PlainAuthenticationRequest": 31,
        "KerberosAuthenticationRequest": 33,
        "GssNegotiationMsg": 34,
        "AuthenticationOkResponse": 38,
        "SessionChangeRequest": 41,
        "SessionChangeResponse": 42,
        "QueryExecuteRequest": 51,
        "QueryReceiptResponse": 52,
        "RowMetadataResponse": 54,
        "RowDataResponse": 56,
        "StatementResponse": 58,
        "QueryExecuteResponse": 60,
        "QueryCancellationRequest": 71,
        "QueryCancellationResponse": 72,
        "QueryProgressRequest": 81,
        "QueryProgressResponse": 82,
        "SessionMonitoringRequest": 91,
        "SessionProtocolVersionResponse": 92,
        "SessionDataResponse": 94,
        "SessionDroppedMessagesResponse": 96,
        "SessionMonitoringResponse": 98,
        "ParseStatementRequest": 101,
        "ParseStatementResponse": 102,
        "StatementBindAndExecuteRequest": 103,
        "ClosePreparedStatementRequest": 105,
        "ClosePreparedStatementResponse": 106,
    }
fix_spec(all_structs)
del all_structs
