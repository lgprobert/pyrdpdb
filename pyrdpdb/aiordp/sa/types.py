# flake8: noqa: E501
from sqlalchemy import types as sqltypes

"""
Type		|    Default interpretation of size / scale / precision
--------------------------------------------------------------------
INTEGER	    |    Precision in decimal digits (if unspecified: 18)
DECIMAL	    |    Precision in decimal digits, scale in decimal digits (if unspecified: 19, 0)
FLOAT		|    Size of mantissa in binary digits (if unspecified: 53)
TIMESTAMP   |
VARCHAR	    |    Physical size in bytes (if unspecifed: variable up to 2G)
VARBINARY	|    Physical size in bytes (if unspecified: variable up to 2G)
Boolean     |
CHAR        |    RDP do not support CHAR, but RDP have a bug can have the deep datasource CHAR type,  I have no idea on this.
"""


class BOOLEAN(sqltypes.BOOLEAN):
    __visit_name__ = "BOOLEAN"


class _NumericType(object):
    """Base for MySQL numeric types.

    This is the base both for NUMERIC as well as INTEGER, hence
    it's a mixin.

    """

    def __init__(self, unsigned=False, zerofill=False, **kw):
        self.unsigned = unsigned
        self.zerofill = zerofill
        super(_NumericType, self).__init__(**kw)


# Do not have TINYINT
class TINYINT(sqltypes.INTEGER):
    __visit_name__ = "TINYINT"


class SMALLINT(sqltypes.SMALLINT):
    __visit_name__ = "SMALLINT"


class INTEGER(sqltypes.INTEGER):
    __visit_name__ = "INTEGER"


class BIGINT(sqltypes.BIGINT):
    __visit_name__ = "INTEGER"


class DECIMAL(sqltypes.DECIMAL):
    __visit_name__ = "DECIMAL"


# class DECIMAL(_NumericType, sqltypes.DECIMAL):
#     """MySQL DECIMAL type."""

#     __visit_name__ = "DECIMAL"

#     def __init__(self, precision=None, scale=None, asdecimal=True, **kw):
#         """Construct a DECIMAL.

#         :param precision: Total digits in this number.  If scale and precision
#           are both None, values are stored to limits allowed by the server.

#         :param scale: The number of digits after the decimal point.

#         :param unsigned: a boolean, optional.

#         :param zerofill: Optional. If true, values will be stored as strings
#           left-padded with zeros. Note that this does not effect the values
#           returned by the underlying database API, which continue to be
#           numeric.

#         """
#         super(DECIMAL, self).__init__(
#             precision=precision, scale=scale, asdecimal=asdecimal, **kw
#         )


class FLOAT(sqltypes.FLOAT):
    __visit_name__ = "FLOAT"


class DATE(sqltypes.DATE):
    __visit_name__ = "DATE"


class TIME(sqltypes.TIME):
    __visit_name__ = "TIME"


class TIMESTAMP(sqltypes.TIMESTAMP):
    __visit_name__ = "TIMESTAMP"


class DATETIME(sqltypes.DateTime):
    __visit_name__ = "DATE"


# Do not have INTERVAL
class INTERVAL(sqltypes.Interval):
    __visit_name__ = "INTERVAL"


class VARCHAR(sqltypes.VARCHAR):
    __visit_name__ = "VARCHAR"


class VARBINARY(sqltypes.VARBINARY):
    __visit_name__ = "VARBINARY"


class CHAR(sqltypes.CHAR):
    __visit_name__ = "CHAR"
