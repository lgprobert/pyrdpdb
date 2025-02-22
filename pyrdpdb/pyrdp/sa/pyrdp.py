# flake8: noqa: E501
"""
.. dialect:: pyrdp
    :name: rapidsdb
    :dbapi: pyrdp
    :connectstring: rapidsdb+pyrdp://<user>:<password>@<host>[:<port>]/<federation>/<catalog>/<schema>
"""
from sqlalchemy.dialects import registry

from .base import RDPDialect


class RDPDialect_pyrdp(RDPDialect):

    driver = "pyrdp"
    default_paramstyle = "format"
    description_encoding = None
    supports_native_decimal = True
    is_async = False
    supports_statement_cache = True
    supports_savepoints = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def import_dbapi(cls):
        from pyrdpdb import pyrdp

        pyrdp.paramstyle = cls.default_paramstyle
        return pyrdp

    def is_disconnect(self, error, connection, cursor):
        """Tells whether connection is closed.

        Parameters:
        - error: not used
        - connection: Optional[Connection]
        - cursor: not use

        Return: bool
        """
        if connection is None:
            return True
        return connection._closed


dialect = RDPDialect_pyrdp

registry.register("rapidsdb.pyrdp", "pyrdpdb.pyrdp.sa.pyrdp", "RDPDialect_pyrdp")
