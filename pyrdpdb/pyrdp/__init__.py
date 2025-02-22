# flake8: noqa: F401
"""
pyrdp: A pure-Python RapidsDB client library.

"""

"""
0	Threads may not share the module.
1	Threads may share the module, but not connections.
2	Threads may share the module and connections.
3	Threads may share the module, connections and cursors.
"""

"""

paramstyle |	Meaning
------------------------------------------------------
qmark	   | Question mark style, e.g. ...WHERE name=?
numeric	   | Numeric, positional style, e.g. ...WHERE name=:1
named	   | Named style, e.g. ...WHERE name=:name
format	   | ANSI C printf format codes, e.g. ...WHERE name=%s
pyformat   | Python extended format codes, e.g. ...WHERE name=%(name)s
"""

from ._version import __version__
from .connections import Connection
from .constants import FIELD_TYPE
from .cursors import Cursor, SSCursor
from .err import *
from .sa.pyrdp import RDPDialect_pyrdp
from .logger import configure_logging

logger = configure_logging()

# dbapi2.0 connection object requires close(), commit(), rollback(), cursor()
# dbapi2.0 optional: autocommit()
# dbapi2.0 optional features: callproc, setinputsizes, setoutputsize

# DBAPI required attributes
threadsafety = 1
# PEP249 is version 2.0; PEP248 is version 1.0, here we follow PEP249
apilevel = "2.0"
paramstyle = "format"


class DBAPISet(frozenset):
    def __ne__(self, other):
        if isinstance(other, set):
            return frozenset.__ne__(self, other)
        else:
            return other not in self

    def __eq__(self, other):
        if isinstance(other, frozenset):
            return frozenset.__eq__(self, other)
        else:
            return other in self

    def __hash__(self):
        return frozenset.__hash__(self)


STRING = DBAPISet(
    [FIELD_TYPE.ENUM, FIELD_TYPE.STRING, FIELD_TYPE.VAR_STRING, FIELD_TYPE.VARCHAR]
)
BINARY = DBAPISet(
    [
        FIELD_TYPE.BLOB,
        FIELD_TYPE.LONG_BLOB,
        FIELD_TYPE.MEDIUM_BLOB,
        FIELD_TYPE.TINY_BLOB,
    ]
)
NUMBER = DBAPISet(
    [
        FIELD_TYPE.DECIMAL,
        FIELD_TYPE.DOUBLE,
        FIELD_TYPE.FLOAT,
        FIELD_TYPE.INT24,
        FIELD_TYPE.LONG,
        FIELD_TYPE.LONGLONG,
        FIELD_TYPE.TINY,
        FIELD_TYPE.YEAR,
    ]
)
DATE = DBAPISet([FIELD_TYPE.DATE, FIELD_TYPE.NEWDATE])
TIME = DBAPISet([FIELD_TYPE.TIME])
TIMESTAMP = DBAPISet([FIELD_TYPE.TIMESTAMP, FIELD_TYPE.DATETIME])
DATETIME = TIMESTAMP
NULL = "NULL"


def Binary(x):
    """Return x as a binary type."""
    return bytes(x)


def connect(*args, **kwargs):
    from .connections import Connection

    return Connection(*args, **kwargs)


__all__ = [
    "BINARY",
    "Binary",
    "Connection",
    "DATE",
    "DATETIME",
    "DataError",
    "DatabaseError",
    "Error",
    "FIELD_TYPE",
    "IntegrityError",
    "InterfaceError",
    "InternalError",
    "RDBError",
    "NULL",
    "NUMBER",
    "NotSupportedError",
    "DBAPISet",
    "OperationalError",
    "ProgrammingError",
    "STRING",
    "TIME",
    "TIMESTAMP",
    "Warning",
    "apilevel",
    "constants",
    "converters",
    "connect",
    "paramstyle",
    "threadsafety",
    "__version__",
]

__path__ = __import__("pkgutil").extend_path(__path__, __name__)
