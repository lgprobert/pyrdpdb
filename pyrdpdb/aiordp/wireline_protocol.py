# -*- coding: utf-8 -*-
import datetime
import errno
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import logging

from thrift import TSerialization
from thrift.protocol import TCompactProtocol

from pyrdpdb.messages.compatibility.ProtocolCompatibleRequest.ttypes import (
    ProtocolCompatibleRequest,
)
from pyrdpdb.messages.compatibility.ProtocolCompatibleResponse.ttypes import (
    ProtocolCompatibleResponse,
)
from pyrdpdb.messages.compatibility.ProtocolIncompatibleResponse.ttypes import (
    ProtocolIncompatibleResponse,
)
from pyrdpdb.messages.v4.AuthenticationOkResponse.ttypes import AuthenticationOkResponse
from pyrdpdb.messages.v4.ClearTextTunnelRequest.ttypes import ClearTextTunnelRequest
from pyrdpdb.messages.v4.ClosePreparedStatementRequest.ttypes import (
    ClosePreparedStatementRequest,
)
from pyrdpdb.messages.v4.ClosePreparedStatementResponse.ttypes import (
    ClosePreparedStatementResponse,
)
from pyrdpdb.messages.v4.ColumnMetadata.ttypes import DataType
from pyrdpdb.messages.v4.DisconnectNotification.ttypes import DisconnectNotification
from pyrdpdb.messages.v4.DisconnectRequest.ttypes import DisconnectRequest
from pyrdpdb.messages.v4.ErrorResponse.ttypes import ErrorResponse
from pyrdpdb.messages.v4.GssNegotiationMsg.ttypes import GssNegotiationMsg
from pyrdpdb.messages.v4.KerberosAuthenticationRequest.ttypes import (
    KerberosAuthenticationRequest,
)
from pyrdpdb.messages.v4.MessageTypes.ttypes import MessageTypes
from pyrdpdb.messages.v4.ParseStatementRequest.ttypes import ParseStatementRequest
from pyrdpdb.messages.v4.ParseStatementResponse.ttypes import ParseStatementResponse

# from .messages.v4.PingRequest.ttypes import PingRequest
# from .messages.v4.PingResponse.ttypes import PingResponse
from pyrdpdb.messages.v4.PlainAuthenticationRequest.ttypes import (
    PlainAuthenticationRequest,
)
from pyrdpdb.messages.v4.QueryExecuteRequest.ttypes import QueryExecuteRequest
from pyrdpdb.messages.v4.QueryExecuteResponse.ttypes import QueryExecuteResponse
from pyrdpdb.messages.v4.QueryProgressRequest.ttypes import QueryProgressRequest
from pyrdpdb.messages.v4.QueryProgressResponse.ttypes import QueryProgressResponse
from pyrdpdb.messages.v4.QueryReceiptResponse.ttypes import (
    QueryReceiptResponse,
    StatementReceipt,
)
from pyrdpdb.messages.v4.RowDataResponse.ttypes import RowDataResponse
from pyrdpdb.messages.v4.RowMetadataResponse.ttypes import RowMetadataResponse
from pyrdpdb.messages.v4.SessionChangeRequest.ttypes import SessionChangeRequest
from pyrdpdb.messages.v4.SessionChangeResponse.ttypes import SessionChangeResponse
from pyrdpdb.messages.v4.SessionDataResponse.ttypes import SessionDataResponse
from pyrdpdb.messages.v4.SessionDroppedMessagesResponse.ttypes import (
    SessionDroppedMessagesResponse,
)
from pyrdpdb.messages.v4.SessionMonitoringRequest.ttypes import SessionMonitoringRequest
from pyrdpdb.messages.v4.SessionMonitoringResponse.ttypes import SessionMonitoringResponse
from pyrdpdb.messages.v4.SessionProtocolVersionResponse.ttypes import (
    SessionProtocolVersionResponse,
)
from pyrdpdb.messages.v4.ShutdownNotification.ttypes import ShutdownNotification
from pyrdpdb.messages.v4.StatementBindAndExecuteRequest.ttypes import (
    StatementBindAndExecuteRequest,
)
from pyrdpdb.messages.v4.StatementResponse.ttypes import StatementResponse
from pyrdpdb.messages.v4.TunnelSupportedResponse.ttypes import TunnelSupportedResponse
from pyrdpdb.messages.v4.WarningResponse.ttypes import WarningResponse

from . import err
from .constants import CR, FIELD_TYPE
from .utils import byte2int, bytes2int, int2_4bytes, int2byte

# from .messages.v2.AuthenticationRequest.ttypes import AuthenticationRequest
# from .messages.v3.QueryCancellationRequest.ttypes import QueryCancellationRequest
# from .messages.v3.QueryCancellationResponse.ttypes import QueryCancellationResponse

log = logging.getLogger("aiordp.wp")

if TYPE_CHECKING:
    from socket import socket

typecode_map = {
    "BOOLEAN": FIELD_TYPE.TINY,
    "INTEGER": FIELD_TYPE.LONG,
    "BIGINT": FIELD_TYPE.LONG,
    "DECIMAL": FIELD_TYPE.DECIMAL,
    "FLOAT": FIELD_TYPE.FLOAT,
    "DATE": FIELD_TYPE.DATE,
    "VARCHAR": FIELD_TYPE.VARCHAR,
    # "VARBINARY": FIELD_TYPE.VARBINARY,
    "TIMESTAMP": FIELD_TYPE.TIMESTAMP,
}


class WirelineProtocol(object):

    MAX_MSG_PAYLOAD_SIZE = 16777208
    # 24 bits - 8 bytes for the header

    def __init__(self, connection=None, tprotocol=None):
        self.connection = connection
        self.sock: socket = connection._sock
        self.rfile = connection._rfile
        self.serialize = TSerialization.serialize
        self.deserialize = TSerialization.deserialize
        self.tprotocol = tprotocol
        self.current_row_data_response: Optional[RowDataResponse] = None
        self.new_row_data_response: Optional[RowDataResponse] = None
        self.has_row_metadata_response = False
        self.current_message_type = None  # current message type
        self.rdb_header = None
        self.icurrent_row_index = 0  # current row index
        self.imax_rows = 0  # total rows of this rowdataresponse packet
        self.row = None  # current row data
        self.numColumns = None  # number of columns
        self.columns = None  # columns metadata
        self.description = None
        self.end_of_response = False  # response end of this request
        self.end_of_results = False  # results end of this request
        self.errstr = None  # ErrorResponse message here
        self.statements: dict = {}
        self.finished_statements: list = []
        self.has_next: bool = False
        self.chunk: Optional[list] = None
        self.chunk_count = 0

        if tprotocol is None:
            self.tprotocol = TCompactProtocol.TCompactProtocolFactory()

    async def login(self):
        """
        Before real request and response, make sure server side have ability to response
        the request.
        """
        await self._do_protocol_compatibility_dailog("login")
        await self._do_tunnel_dialog()
        # Authentication
        if self.connection.auth_type == "PLAIN":
            await self._do_plain_authentication_dialog()
        else:
            raise err.NotSupportedError("Only support Authentication type PLAIN")

        await self._do_session_change_dialog()

    async def _do_protocol_compatibility_dailog(self, desc):
        """
        Negotiate protocol version
        """
        request = ProtocolCompatibleRequest(4, desc)
        await self._send_message(request, 1)
        message = await self._read_message()
        return message

    async def _do_tunnel_dialog(self):
        """
        Negotiate tunnel type
        """
        request = ClearTextTunnelRequest()
        await self._send_message(request, 21)
        message = await self._read_message()
        return message

    def _do_kerberos_authentication_dialog(self):
        """
        Authentication with kerberos, still not support here.
        """
        pass

    async def _do_plain_authentication_dialog(self):
        """
        Authentication with username and password.
        """
        username = self.connection.user
        password = self.connection.password
        request = PlainAuthenticationRequest(username, password)
        await self._send_message(request, 31)
        message = await self._read_message()

        if message.type == 6:
            log.error("Could not authenticate with RapidsDB (username/password).")
            # throw a exception
            raise err.OperationalError(message.message.errorString, "28R01")

    # async def _do_authentication_dialog(self, username):
    #     """
    #     Authentication, actually server side always allow client pass the authentication
    #     right now.
    #     """
    #     request = AuthenticationRequest(username)
    #     await self._send_message(request, 23)
    #     message = await self._read_message()
    #     return message

    async def _do_session_change_dialog(self):
        """
        I have no idea about this method, seems we need this request befor real
        comunication.
        """
        request = SessionChangeRequest()
        await self._send_message(request, 41)
        message = await self._read_message()
        return message

    async def query(self, sql):
        """
        Send query message and handle response.
        """
        # clear last result here
        self._clear()
        self.current_message_type = MessageTypes.QueryExecuteRequest

        request = QueryExecuteRequest(query=sql)
        await self._send_message(request, 51)

        await self._process_state_transitions()

        if self.new_row_data_response is not None:
            self.current_row_data_response = self.new_row_data_response

    async def _read_message(self):
        """
        Read a message from sever side. First read a message header , according to the
        header info, the read the total message.
        """
        header = await self._read_bytes(8)
        length = bytes2int(header[0:4])[0]
        return_type = byte2int(header[4])
        payload_size = length - 8
        payload = await self._read_bytes(payload_size)
        message = self._create_message(return_type)
        return_message = self.deserialize(message, payload, self.tprotocol)

        msgTypeName = self._get_messagetype_name(return_type)
        msg = (
            "Receving Message type: "
            + str(return_type)
            + " ("
            + msgTypeName
            + ") from server."
        )

        log.debug(msg)
        return MessageAndTypePair(return_message, return_type)

    async def _read_bytes(self, num_bytes):
        """
        Read bytes from socket.
        """
        while True:
            try:
                data = self.rfile.read(num_bytes)
                break
            except (IOError, OSError) as e:
                if e.errno == errno.EINTR:
                    continue
                raise err.OperationalError(
                    CR.CR_SERVER_LOST,
                    "Lost connection to RapidDB server during query (%s)" % (e,),
                )
        if len(data) < num_bytes:
            raise err.OperationalError(
                CR.CR_SERVER_LOST,
                "Lost connection to RapidDB server during query ",
            )
        return data

    async def _send_message(self, message, type):
        """
        Send  message to server side.
        """

        msgTypeName = self._get_messagetype_name(type)
        msg = f"Sending Message type: {str(type)} ({msgTypeName}) to server. "

        # log message info
        log.debug(msg)

        message_bytes = TSerialization.serialize(message, self.tprotocol)
        if len(message_bytes) > self.MAX_MSG_PAYLOAD_SIZE:
            raise err.ProgrammingError("Message is over max message payload size.")

        header = self._create_header(type, len(message_bytes))
        data = header + message_bytes
        self._send_bytes(data)

    def _send_bytes(self, data):
        """
        Send bytes to socket.
        """

        try:
            self.sock.sendall(data)
        except IOError as e:
            raise err.OperationalError(
                CR.CR_SERVER_GONE_ERROR,
                "RapidDB server has gone away (%r)" % (e,),
            )

    def _get_messagetype_name(self, type):
        """
        Get message type name according type id.
        """
        message_type_name = MessageTypes._VALUES_TO_NAMES[type]
        if message_type_name is None:
            raise err.ProgrammingError("Message type not exist.")
        return message_type_name

    def _query_metadata_response_handler(self, meta_message: RowMetadataResponse):
        self.has_next = True
        self.numColumns = meta_message.numColumns
        column_metadatas = meta_message.columns
        columns = []
        descs = []
        # sqlAlchemly only support list description
        for column_metadata in column_metadatas:
            col_info = {}
            desc = []
            col_info["name"] = column_metadata.columnName
            col_info["type"] = column_metadata.columnType
            col_info["rdb_type"] = self._get_rdb_type(column_metadata.columnType)
            col_info["precision"] = column_metadata.precision
            col_info["scale"] = column_metadata.scale
            col_info["nullable"] = column_metadata.isNullable
            # change 'type' to DBAPI 2.0 compliant type code
            col_info["type"] = typecode_map.get(col_info["rdb_type"].upper()) or 0
            desc.append(col_info["name"])
            desc.append(col_info["type"])
            desc.append(col_info["rdb_type"])
            desc.append(col_info["precision"])
            desc.append(col_info["scale"])
            desc.append(col_info["nullable"])
            columns.append(col_info)
            descs.append(tuple(desc))
        self.columns = columns
        self.description = tuple(descs)
        self.has_row_metadata_response = True
        self.imax_rows = 0
        self.icurrent_row_index = 0
        if self.numColumns > 0:
            self.end_of_response = False
            self.end_of_results = False

    def new_state_error_response_handler(self, response_pair) -> bool:
        # - errorCode
        # - sqlStateCode
        # - errorString
        # - stackTrace
        self._error_received = True
        message = response_pair.message
        self.errstr = message.errorString
        if message.stackTrace:
            self.errstr += "\n" + message.stackTrace
        b_done = True
        self.end_of_response = True
        return b_done

    def query_execute_request_handler(self, new_state, response_pair) -> bool:
        b_done = False
        if new_state == MessageTypes.QueryReceiptResponse:
            _receipt: QueryReceiptResponse = response_pair.message
            # self.statements = _receipt.statementReceipts
            stmt_receipt: StatementReceipt
            for stmt_receipt in _receipt.statementReceipts:
                self.statements[stmt_receipt.statementId] = {
                    "stmt": stmt_receipt.statementString,
                    "key": stmt_receipt.statementKey,
                }
        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        else:
            # raise a execption to tell wrong state
            pass
        return b_done

    def query_receipt_response_handler(self, new_state, response_pair) -> bool:
        b_done = False
        if new_state == MessageTypes.RowMetadataResponse:
            self._query_metadata_response_handler(response_pair.message)
        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        elif new_state == MessageTypes.StatementResponse:
            pass
        else:
            # TODO raise a execption to tell wrong state
            pass
        return b_done

    def row_metadata_response_handler(self, new_state, response_pair) -> bool:
        b_done = False
        if new_state == MessageTypes.RowDataResponse:
            row_message: RowDataResponse = response_pair.message
            # self.icurrent_row_index = 0
            self.imax_rows = len(row_message.rows)
            self.new_row_data_response = row_message
            self.end_of_response = False
        elif new_state == MessageTypes.StatementResponse:
            # stmt_message = response_pair.message
            self.imax_rows = 0
        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        else:
            # TODO raise a execption to tell wrong state
            pass
        return b_done

    def row_data_response_handler(self, new_state, response_pair, b_done) -> bool:
        if new_state == MessageTypes.RowDataResponse:
            self.end_of_response = False
            b_done = True
        elif new_state == MessageTypes.StatementResponse:
            """
            statementId
            statementString
            numMatchedRows
            numAffectedRows
            affectedVerb
            """
            stmt_message: StatementResponse = response_pair.message
            self.affected_rows = stmt_message.numAffectedRows
            self.finished_statements.append(stmt_message.statementId)
            if set(self.finished_statements) == set(self.statements.keys()):
                self.has_next = False

        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        else:
            # TODO raise a execption to tell wrong state
            pass
        return b_done

    def statement_response_handler(self, new_state, response_pair) -> bool:
        b_done = False
        if new_state == MessageTypes.QueryExecuteResponse:
            b_done = True
            self.end_of_response = True
            self.has_next = False
        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        # TODO: Handle receiving another StatementResponse here
        # TODO: e.g., as part of a batch submitted as one query.
        elif new_state == MessageTypes.RowMetadataResponse:
            self._query_metadata_response_handler(response_pair.message)
        # do not handle multiple results
        elif new_state == MessageTypes.StatementResponse:
            pass
        else:
            # TODO raise a execption to tell wrong state
            self.has_next = False
        return b_done

    def query_execute_response_handler(self, new_state, response_pair) -> bool:
        # self.new_row_data_response = None
        # self.current_row_data_response = None
        # self.icurrent_row_index = 0
        # self.imax_rows = 0
        # self.numColumns = 0
        # self.columns = None
        # self.description = None
        # self.errstr = None
        # self.finished_statements = []
        # self.statements = {}
        # self.end_of_response = True
        # self.end_of_results = True
        # return True
        pass

    def error_response_handler(self, new_state, response_pair) -> bool:
        b_done = False
        if new_state == MessageTypes.QueryExecuteResponse:
            b_done = True
            self.end_of_response = True
        elif new_state == MessageTypes.WarningResponse:
            pass
        elif new_state == MessageTypes.ErrorResponse:
            b_done = self.new_state_error_response_handler(response_pair)
        else:
            # TODO raise a execption to tell wrong state
            pass
        return b_done

    async def _handle_message_state(self):
        """Handle response from database server side."""
        b_done = False
        response_pair = None
        new_state = None

        new_state = await self._read_rdp_header()
        log.debug(
            "Receive Message type: {} ({}) from server.".format(
                str(new_state), self._get_messagetype_name(new_state)
            )
        )

        if (
            self.current_message_type == MessageTypes.RowDataResponse
            and new_state == MessageTypes.RowDataResponse
        ):
            b_done = True
        else:
            response_pair = await self._read_rdp_buffer()

        # log.debug(f"message: {response_pair.message}")

        if self.current_message_type == MessageTypes.QueryExecuteRequest:
            b_done = self.query_execute_request_handler(new_state, response_pair)
        elif self.current_message_type == MessageTypes.QueryReceiptResponse:
            b_done = self.query_receipt_response_handler(new_state, response_pair)
        elif self.current_message_type == MessageTypes.RowMetadataResponse:
            b_done = self.row_metadata_response_handler(new_state, response_pair)
        elif self.current_message_type == MessageTypes.RowDataResponse:
            b_done = self.row_data_response_handler(new_state, response_pair, b_done)
        elif self.current_message_type == MessageTypes.StatementResponse:
            b_done = self.statement_response_handler(new_state, response_pair)
        elif self.current_message_type == MessageTypes.QueryExecuteResponse:
            b_done = self.query_execute_response_handler(new_state, response_pair)
        elif self.current_message_type == MessageTypes.WarningResponse:
            # All warnings are handled in the context of other queries, and we ignore
            # warnings from the context
            # of setting current_message_type too. So we should never get here.
            pass
        elif self.current_message_type == MessageTypes.ErrorResponse:
            b_done = self.error_response_handler(new_state, response_pair)
        else:
            b_done = True

        self.rdb_header.msg_prior_type = self.current_message_type
        self.current_message_type = new_state

        return b_done

    # TODO: extracte repeat part
    def _handle_error_response(self):
        pass

    def _get_rdb_type(self, colum_type):
        """
        Get pyrdpdb data type according to metadata colum type.
        :param number colum_type : colum data type.
        : return : pyrdpdb data type.
        """
        return DataType._VALUES_TO_NAMES[colum_type]

    def has_next_row(self) -> bool:
        return self.icurrent_row_index < self.imax_rows

    async def get_next_row(self):
        """
        Get next row data.
        : return : flag of if have next row.
        """
        if (
            self.end_of_response or self.end_of_results
        ) and self.current_row_data_response is None:
            return False
        if self.icurrent_row_index < self.imax_rows:
            await self._next_row()
        else:
            read_data = await self._read_more_data()
            if read_data:
                self.icurrent_row_index = 0
                self.end_of_results = False
                await self._next_row()
            else:
                self.end_of_response = True
                self.end_of_results = True
        if self.end_of_results:
            return False
        return True

    async def to_pandas(self) -> bool:
        """Generate self._df dataframe from data batch."""

        if (
            self.end_of_response or self.end_of_results
        ) and self.current_row_data_response is None:
            return False

        self._df = None

        if self.icurrent_row_index < self.imax_rows:
            df = self._next_set_column()
        else:
            more_data = await self._read_more_data()
            if more_data:
                self.icurrent_row_index = 0
                self.end_of_results = False
                df = await self._next_set_column()
            else:
                self.end_of_response = True
                self.end_of_results = True
        if self.end_of_results:
            return False
        self._df = df
        return True

    async def _next_set_column(self):
        """
        Decode all buffered data to a set.
        """
        import pandas as pd

        if self.end_of_response and self.current_row_data_response is None:
            return

        self.chunk = []
        columns = [desc[0] for desc in self.description]
        column_dict = {col: [] for col in columns}
        while self.icurrent_row_index < self.imax_rows:
            row = self.current_row_data_response.rows[self.icurrent_row_index]
            self.icurrent_row_index += 1
            row_columns = row.columns
            for col_idx, value in enumerate(row_columns):
                col_name = columns[col_idx]
                col_type = self.columns[col_idx]["rdb_type"]
                value = row_columns[col_idx]
                _new_value = self.convert_db_value(value, col_type)
                column_dict[col_name].append(_new_value)

        df = pd.DataFrame(column_dict)
        return df

    def convert_db_value(self, value, rdb_type):
        if value is None:
            return None
        elif rdb_type == "BOOLEAN":
            return value.booleanVal
        elif rdb_type == "TINYINT":
            return value.tinyIntVal
        elif rdb_type == "SMALLINT":
            return value.smallIntVal
        elif rdb_type == "INTEGER":
            return value.integerVal
        elif rdb_type == "BIGINT":
            return value.bigintVal
        elif rdb_type == "DECIMAL":
            return Decimal(value.bigDecimalVal)
        elif rdb_type == "FLOAT":
            return value.doubleVal
        elif rdb_type == "DATE":
            ts = value.dateVal
            return datetime.date(year=ts.year, month=ts.month, day=ts.day)
        elif rdb_type == "TIME":
            ts = value.timeVal
            return datetime.time(
                hour=ts.hour,
                minute=ts.minute,
                second=ts.second,
                microsecond=int(ts.nanoseconds / 1000),
            )
        elif rdb_type == "TIMESTAMP":
            ts = value.timestampVal
            return datetime.datetime(
                ts.year,
                ts.month,
                ts.day,
                ts.hour,
                ts.minute,
                ts.second,
                int(ts.nanoseconds / 1000),
            )
        elif rdb_type == "INTERVAL":
            return value.intervalVal
        elif rdb_type == "VARCHAR":
            return value.stringVal
        elif rdb_type == "VARBINARY":
            return value.binaryVal
        else:
            raise ValueError(f"Unsupported data type: {rdb_type}")

    async def get_next_set(self):
        """
        Get next set data.
        """
        if (
            self.end_of_response or self.end_of_results
        ) and self.current_row_data_response is None:
            self.row = None
            self.chunk = None
            return False

        if self.icurrent_row_index < self.imax_rows:
            await self._next_set()
        else:
            more_data = await self._read_more_data()
            if more_data:
                self.icurrent_row_index = 0
                self.end_of_results = False
                await self._next_set()
                log.debug(f"chunk size: {len(self.chunk)}")
            else:
                self.end_of_response = True
                self.end_of_results = True
        if self.end_of_results:
            return False
        return True

    async def _next_set(self):
        """
        Decode all buffered data to a set.
        """
        if self.end_of_response and self.current_row_data_response is None:
            return

        self.chunk = []
        while not await self._get_row_from_rdp_buffer():
            self.chunk.append(self.row)

    async def _next_row(self):
        """
        Decode next row from buffer.
        """
        if self.end_of_response and self.current_row_data_response is None:
            return

        await self._get_row_from_rdp_buffer()

    async def _get_row_from_rdp_buffer(self):
        """Run row protocol conversion and return True if there is no more records
        in buffer and False otherwise.

        Note: each time one row is read from buffer, convert column data types
        from RDP to python, save row to self.row.
        """
        if (
            self.current_row_data_response is not None
            and self.icurrent_row_index < self.imax_rows
        ):
            row = self.current_row_data_response.rows[self.icurrent_row_index]
            self.icurrent_row_index += 1
            columns = row.columns
            temp_row = []
            for i in range(len(columns)):
                if columns[i].isNull:
                    temp_row.append(None)
                elif self.columns[i]["rdb_type"] == "NULL":
                    temp_row.append(None)
                elif self.columns[i]["rdb_type"] == "BOOLEAN":
                    temp_row.append(columns[i].booleanVal)
                elif self.columns[i]["rdb_type"] == "TINYINT":
                    temp_row.append(columns[i].tinyIntVal)
                elif self.columns[i]["rdb_type"] == "SMALLINT":
                    temp_row.append(columns[i].smallIntVal)
                elif self.columns[i]["rdb_type"] == "INTEGER":
                    temp_row.append(columns[i].integerVal)
                elif self.columns[i]["rdb_type"] == "BIGINT":
                    temp_row.append(columns[i].bigintVal)
                elif self.columns[i]["rdb_type"] == "DECIMAL":
                    temp_row.append(Decimal(columns[i].bigDecimalVal))
                    # temp_row.append(colums[i].bigDecimalVal)
                elif self.columns[i]["rdb_type"] == "FLOAT":
                    temp_row.append(columns[i].doubleVal)
                elif self.columns[i]["rdb_type"] == "DATE":
                    ts = columns[i].dateVal
                    date_val = datetime.date(year=ts.year, month=ts.month, day=ts.day)
                    temp_row.append(date_val)
                elif self.columns[i]["rdb_type"] == "TIME":
                    ts = columns[i].timeVal
                    time_val = datetime.time(
                        hour=ts.hour,
                        minute=ts.minute,
                        second=ts.second,
                        microsecond=int(ts.nanoseconds / 1000),
                    )
                    temp_row.append(time_val)
                elif self.columns[i]["rdb_type"] == "TIMESTAMP":
                    # ts type: ..messages.v4.ColumnValue.ttypes.Timestamp
                    ts = columns[i].timestampVal
                    dt = datetime.datetime(
                        ts.year,
                        ts.month,
                        ts.day,
                        ts.hour,
                        ts.minute,
                        ts.second,
                        int(ts.nanoseconds / 1000),  # to microsecond
                    )
                    temp_row.append(dt)
                elif self.columns[i]["rdb_type"] == "INTERVAL":
                    interval = columns[i].intervalVal
                    temp_row.append(interval)
                elif self.columns[i]["rdb_type"] == "VARCHAR":
                    temp_row.append(columns[i].stringVal)
                elif self.columns[i]["rdb_type"] == "VARBINARY":
                    temp_row.append(columns[i].binaryVal)
                else:
                    raise err.NotSupportedError(
                        "Unimplemented data type from the wire line protocol: {}".format(
                            self.columns[i]["rdb_type"]
                        )
                    )
            self.row = tuple(temp_row)
            self.end_of_results = False
            return False
        else:
            self.end_of_results = True
            return True

    async def _read_more_data(self):
        """
        Read more data.
        : return : flag of the response state.
        """
        self.chunk_count += 1
        log.debug(f"Reading batch {self.chunk_count}.")

        b_done = False
        self.current_row_data_response = None

        if self.end_of_response:
            return False
        response_pair = None
        prior_state = self.rdb_header.msg_prior_type
        new_state = self.rdb_header.msg_type

        if (
            prior_state == MessageTypes.RowDataResponse
            and new_state == MessageTypes.RowDataResponse
            and self.end_of_response is False
        ):
            response_pair = await self._read_rdp_buffer()
            row_data_response: RowDataResponse = response_pair.message
            self.imax_rows = len(row_data_response.rows)
            self.current_row_data_response = row_data_response
            self.icurrent_row_index = 0
            b_done = True
        else:
            return False

        self.current_message_type = new_state
        await self._process_state_transitions()

        return b_done

    async def _process_state_transitions(self):
        """Process Thrift server message state transitions until all message responses
        are finished."""
        done = False
        while not done:
            done = await self._handle_message_state()

    async def _read_rdp_header(self):
        """
        Read 8 bytes from socket and resolv the message meta information.
        : return : message type id.
        """
        header = await self._read_bytes(8)
        length = bytes2int(header[0:4])[0]
        return_type = byte2int(header[4])
        payload_size = length - 8

        if self.rdb_header is None:
            self.rdb_header = RDPHeader()
        self.rdb_header.raw_msg_type = return_type
        self.rdb_header.msg_type = return_type
        self.rdb_header.msg_length = payload_size
        self.rdb_header.clear()

        return return_type

    async def _read_rdp_buffer(self):
        """
        Read message boay according to message payload size.
        : return : MessageAndTypePair.
        """
        payload_size = self.rdb_header.msg_length
        payload = await self._read_bytes(payload_size)
        message = self._create_message(self.rdb_header.raw_msg_type)
        self.deserialize(message, payload, self.tprotocol)
        return MessageAndTypePair(message, self.rdb_header.raw_msg_type)

    def _create_header(self, type, size):
        """
        Create byte mesage header.
        :param number type : message type id.
        :param number size : message paload size.
        : return : bytes of message header.
        """
        header = (
            int2_4bytes(size + 8)
            + int2byte(type)
            + int2byte(0)
            + int2byte(0)
            + int2byte(0)
        )
        return header

    def _create_message(self, type):
        """
        Create empty message according to message type id.
        :param number type : message type id.
        : return : Empty message of the type id.
        """

        if type == 1:
            return ProtocolCompatibleRequest()
        elif type == 2:
            return ProtocolCompatibleResponse()
        elif type == 4:
            return ProtocolIncompatibleResponse()
        elif type == 6:
            return ErrorResponse()
        elif type == 8:
            return WarningResponse()
        elif type == 10:
            return ShutdownNotification()
        elif type == 12:
            return DisconnectNotification()
        elif type == 13:
            return DisconnectRequest()
        elif type == 15:
            return DisconnectRequest()
        elif type == 16:
            return DisconnectRequest()
        elif type == 21:
            return ClearTextTunnelRequest()
        elif type == 22:
            return TunnelSupportedResponse()
        elif type == 31:
            return PlainAuthenticationRequest()
        elif type == 33:
            return KerberosAuthenticationRequest()
        elif type == 34:
            return GssNegotiationMsg()
        elif type == 38:
            return AuthenticationOkResponse()
        elif type == 41:
            return SessionChangeRequest()
        elif type == 42:
            return SessionChangeResponse()
        elif type == 51:
            return QueryExecuteRequest()
        elif type == 52:
            return QueryReceiptResponse()
        elif type == 54:
            return RowMetadataResponse()
        elif type == 56:
            return RowDataResponse()
        elif type == 58:
            return StatementResponse()
        elif type == 60:
            return QueryExecuteResponse()
        # elif type == 71:
        #     return QueryCancellationRequest()
        # elif type == 72:
        #     return QueryCancellationResponse()
        elif type == 81:
            return QueryProgressRequest()
        elif type == 82:
            return QueryProgressResponse()
        elif type == 91:
            return SessionMonitoringRequest()
        elif type == 92:
            return SessionProtocolVersionResponse()
        elif type == 94:
            return SessionDataResponse()
        elif type == 96:
            return SessionDroppedMessagesResponse()
        elif type == 98:
            return SessionMonitoringResponse()
        elif type == 101:
            return ParseStatementRequest()
        elif type == 102:
            return ParseStatementResponse()
        elif type == 103:
            return StatementBindAndExecuteRequest()
        elif type == 105:
            return ClosePreparedStatementRequest()
        elif type == 106:
            return ClosePreparedStatementResponse()
        else:
            return None

    def _clear(self):
        self.errstr = None
        self.row = None
        self.numColumns = None
        self.columns = None
        self.description = None
        # self.end_of_response = False
        # self.end_of_results = False
        self.statements = {}
        self.finished_statements = []
        self.has_next = False
        self.chunk = None
        self.chunk_count = 0
        self.icurrent_row_index = 0
        self.imax_rows = 0
        # self.current_message_type = None
        # self.rdb_header = None
        self.current_row_data_response = None
        # self.new_row_data_response = None
        # self.has_row_metadata_response = False


class RDPHeader(object):
    def __init__(
        self,
        message=None,
        msg_type=None,
        msg_prior_type=None,
        raw_msg_type=None,
        msg_length=None,
    ):
        self.message = message
        self.msg_type = msg_type
        self.msg_prior_type = msg_prior_type
        self.raw_msg_type = raw_msg_type
        self.msg_length = msg_length

    def clear(self):
        self.message = None


class MessageAndTypePair(object):
    """Message and message type wrapper."""

    def __init__(self, message, type):
        self.message = message
        self.type = type


class TableMetaData(object):
    def __init__(self):
        self.catalog = None
        self.schema = None
        self.name = None
