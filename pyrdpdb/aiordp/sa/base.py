# flake8: noqa: E501
from typing import TYPE_CHECKING, Any, Optional, Type

from sqlalchemy import exc, types, util
from sqlalchemy.engine import default, reflection
from sqlalchemy.sql import compiler, sqltypes
from sqlalchemy.sql import text as satext
from sqlalchemy.sql.elements import quoted_name

from . import types as RDP_types

if TYPE_CHECKING:
    from sqlalchemy.engine.url import URL

str_type_map = {
    "BOOLEAN": sqltypes.BOOLEAN,
    "INTEGER": sqltypes.INTEGER,
    "DECIMAL": sqltypes.DECIMAL,
    "FLOAT": sqltypes.FLOAT,
    "DATE": sqltypes.DATE,
    "VARCHAR": sqltypes.VARCHAR,
    "VARBINARY": sqltypes.VARBINARY,
    "TIMESTAMP": sqltypes.TIMESTAMP,
}

# All keywords from parser file, and not sure if all keyword include in below.
RESERVED_WORDS = {
    "add",
    "all",
    "and",
    "as",
    "asc",
    "between",
    "both",
    "by",
    "catalog",
    "connector",
    "corresponding",
    "create",
    "cross",
    "current_catalog",
    "current_federation",
    "current_schema",
    "current_timestamp",
    "data",
    "date",
    "delete",
    "desc",
    "disabled",
    "distinct",
    "drop",
    "enabled",
    "enable",
    "escape",
    "except",
    "false",
    "federation",
    "for",
    "full",
    "from",
    "group",
    "having",
    "in",
    "index",
    "insert",
    "intersect",
    "into",
    "is",
    "join",
    "leading",
    "left",
    "like",
    "limit",
    "no",
    "node",
    "not",
    "now",
    "null",
    "offset",
    "on",
    "or",
    "order",
    "outer",
    "over",
    "overlay",
    "partition",
    "reference",
    "refresh",
    "right",
    "schema",
    "select",
    "set",
    "stats",
    "statistics",
    "table",
    "timestamp",
    "top",
    "true",
    "union",
    "update",
    "using",
    "where",
    "with",
    "boolean",
    "decimal",
    "float",
    "integer",
    "to",
    "trailing",
    "type",
    "values",
    "varbinary",
    "varchar",
    "abs",
    "array_element",
    "array_length",
    "avg",
    "case",
    "cast",
    "ceiling",
    "ceil",
    "char",
    "char_length",
    "coalesce",
    "concat",
    "count",
    "day",
    "dayofmonth",
    "dayofweek",
    "dayofyear",
    "decode",
    "else",
    "end",
    "exists",
    "exp",
    "extract",
    "field",
    "floor",
    "format_currency",
    "from_unixtime",
    "hour",
    "if",
    "ifnull",
    "interval",
    "key",
    "lower",
    "ltrim",
    "max",
    "min",
    "minute",
    "mod",
    "monotonic",
    "month",
    "nullif",
    "octet_length",
    "position",
    "pow",
    "power",
    "primary",
    "quarter",
    "rand",
    "repeat",
    "replace",
    "round",
    "row_number",
    "rtrim",
    "second",
    "set_field",
    "since_epoch",
    "space",
    "sqrt",
    "stddev",
    "stddev_pop",
    "stddev_samp",
    "substr",
    "substring",
    "sum",
    "then",
    "to_dtinterval",
    "to_timestamp",
    "to_yminterval",
    "trim",
    "truncate",
    "typeof",
    "unique",
    "upper",
    "variance",
    "var_pop",
    "var_samp",
    "week",
    "weekday",
    "weekofyear",
    "when",
    "xtypeof",
    "year",
    "hint_start",
    "hint_end",
    "block",
    "bloom",
    "btree",
    "hash",
    "loop",
    "skiplist",
    "tree",
    "value",
    "__timestamp",
}

# __timestamp is a magic word for superset

# replace sqlalchemy defined data type
colspecs = {
    types.BOOLEAN: RDP_types.BOOLEAN,
    types.INTEGER: RDP_types.INTEGER,
    types.DECIMAL: RDP_types.DECIMAL,
    types.FLOAT: RDP_types.FLOAT,
    types.TIMESTAMP: RDP_types.DATETIME,
    types.VARCHAR: RDP_types.VARCHAR,
    types.DateTime: RDP_types.DATETIME,
    types.VARBINARY: RDP_types.VARBINARY,
    types.DATETIME: RDP_types.DATETIME,
    types.DATE: RDP_types.DATE,
}

# ?
ischema_names = {
    "boolean": RDP_types.BOOLEAN,
    "integer": RDP_types.INTEGER,
    "decimal": RDP_types.DECIMAL,
    "float": RDP_types.FLOAT,
    "datetime": RDP_types.DATETIME,
    "varchar": RDP_types.VARCHAR,
    "varbinary": RDP_types.VARBINARY,
}

type_map: dict[int, Any] = {
    0: sqltypes.NULLTYPE,
    1: sqltypes.BOOLEAN,
    2: sqltypes.INTEGER,
    3: sqltypes.SMALLINT,
    4: sqltypes.INTEGER,
    5: sqltypes.INTEGER,
    6: sqltypes.DECIMAL,
    7: sqltypes.FLOAT,
    8: sqltypes.DATE,
    9: sqltypes.TIME,
    10: sqltypes.TIMESTAMP,
    11: sqltypes.Interval,
    12: sqltypes.VARCHAR,
    13: sqltypes.VARBINARY,
}


class RDPIdentifierPreparer(compiler.IdentifierPreparer):

    reserved_words = RESERVED_WORDS

    def __init__(
        self,
        dialect,
        server_ansiquotes=False,
        quote_case_sensitive_collations=False,
        **kw,
    ):

        quote = '"'

        # super(RDPIdentifierPreparer, self).__init__(
        super().__init__(
            dialect,
            initial_quote=quote,
            escape_quote=quote,
            quote_case_sensitive_collations=quote_case_sensitive_collations,
        )

    def format_table(self, table, use_schema=True, name=None):
        """Prepare a quoted table and schema name."""
        if name is None:
            name = table.name

        # 加引号可以保证 表明区分大小写
        # result = self.quote(name)
        result = '"' + name + '"'

        effective_schema = self.schema_for_object(table)

        if effective_schema is None:
            effective_schema = self.dialect.default_schema_name.upper()

        if not self.omit_schema and use_schema and effective_schema:
            result = self.quote_schema(effective_schema) + "." + result

        # RDP support catalog
        catalog = self._get_catalog()

        if catalog:
            result = self._quote_catalog(catalog) + "." + result

        return result

    # def format_column(
    #     self,
    #     column,
    #     use_table=False,
    #     name=None,
    #     table_name=None,
    #     use_schema=False,
    # ):
    #     if name is None:
    #         name = column.name
    #     if name.lower() in self.reserved_words:
    #         name = name.upper()
    #     if not getattr(column, "is_literal", False):
    #         if use_table:
    #             return (
    #                 self.format_table(
    #                     column.table, use_schema=use_schema, name=table_name
    #                 )
    #                 + "."
    #                 + self.quote(name)
    #             )
    #         else:
    #             return self.quote(name)
    #     else:
    #         if use_table:
    #             return (
    #                 self.format_table(
    #                     column.table, use_schema=use_schema, name=table_name
    #                 )
    #                 + "."
    #                 + name
    #             )
    #         else:
    #             return name

    def _quote_catalog(self, catalog):
        return catalog

    def _get_catalog(self):
        return self.dialect.default_catalog_name


class RDPStatementCompiler(compiler.SQLCompiler):
    reserved_words = RESERVED_WORDS

    def visit_table(self, table, **kwargs):
        """table is a Table object"""
        effective_schema = self.preparer.schema_for_object(table)
        table.name = quoted_name(table.name, True)
        if not effective_schema:
            effective_schema = self.dialect.default_schema_name
        ret = (
            self.preparer.quote_schema(effective_schema)
            + "."
            + self.preparer.quote_identifier(table.name)
        )
        return ret

    def visit_column(self, column, add_to_result_map=None, include_table=True, **kwargs):
        name = orig_name = column.name
        if name is None:
            name = self._fallback_column_name(column)

        # TODO  visit_column and format_column need handle this
        if name.lower() in self.reserved_words:
            name = name.upper()

        is_literal = column.is_literal
        # if not is_literal and isinstance(name, elements._truncated_label):
        #     name = self._truncated_identifier("colident", name)

        if add_to_result_map is not None:
            add_to_result_map(name, orig_name, (column, name, column.key), column.type)

        if is_literal:
            name = self.escape_literal_column(name)
        else:
            name = self.preparer.quote(name)

        if column.table is not None:
            table_name = column.table.name
            name = self.preparer.quote_identifier(table_name) + "." + name
        return name

    def limit_clause(self, select, **kwargs):
        text = ""
        if select._limit_clause is not None:
            text += "\n LIMIT " + self.process(select._limit_clause, **kwargs)
        if select._offset_clause is not None:
            if select._limit_clause is None:
                # 2147384648 is the max. no. of records per result set
                text += "\n LIMIT 2147384648"
            text += " OFFSET " + self.process(select._offset_clause, **kwargs)
        return text


class RDPTypeCompiler(compiler.GenericTypeCompiler):

    def visit_BOOLEAN(self, type_, **kw):
        # type_.create_constraint = False
        return "BOOLEAN"

    def visit_TINYINT(self, type_, **kw):
        # if type_.display_width is not None:
        #     return "TINYINT(%s)" % type_.display_width
        # else:
        return "TINYINT"

    def visit_SMALLINT(self, type_, **kw):
        # if type_.display_width is not None:
        #     return "SMALLINT(%(display_width)s)" % {'display_width': type_.display_width}
        # else:
        return "SMALLINT"

    def visit_INTEGER(self, type_, **kw):
        # if type_.display_width is not None:
        #     return  "INTEGER(%(display_width)s)" % {'display_width': type_.display_width}
        # else:
        return "INTEGER"

    def visit_BIGINT(self, type_, **kw):
        # if type_.display_width is not None:
        #     return "BIGINT(%(display_width)s)" % {'display_width': type_.display_width}
        # else:
        return "INTEGER"

    def visit_DECIMAL(self, type_, **kw):
        if type_.precision is None:
            return "DECIMAL"
        elif type_.scale is None:
            return "DECIMAL(%(precision)s)" % {"precision": type_.precision}
        else:
            return "DECIMAL(%(precision)s, %(scale)s)" % {
                "precision": type_.precision,
                "scale": type_.scale,
            }

    def visit_FLOAT(self, type_, **kw):
        if type_.scale is not None and type_.precision is not None:
            return "FLOAT(%s, %s)" % (type_.precision, type_.scale)
        elif type_.precision is not None:
            return "FLOAT(%s)" % (type_.precision,)
        else:
            return "FLOAT"

    def visit_NUMERIC(self, type_, **kw):
        return self.visit_DECIMAL(type_, **kw)

    def visit_DATE(self, type_, **kw):
        return "DATE"

    def visit_TIME(self, type_, **kw):
        if getattr(type_, "fsp", None):
            return "TIME(%d)" % type_.fsp
        else:
            return "TIME"

    def visit_TIMESTAMP(self, type_, **kw):
        # print("robin-timestamp")
        if getattr(type_, "fsp", None):
            return "TIMESTAMP(%d)" % type_.fsp
        else:
            return "TIMESTAMP"

    def visit_VARCHAR(self, type_, **kw):
        if type_.length:
            return "VARCHAR(%d)" % type_.length
        else:
            return "VARCHAR"

    def visit_VARBINARY(self, type_, **kw):
        return "VARBINARY(%d)" % type_.length

    def visit_CHAR(self, type_, **kw):
        return "CHAR"

    # RDP do not support DateTime, this is just past some test case
    def visit_DATETIME(self, type_, **kw):
        return "DATE"

    def visit_TEXT(self, type_, **kw):
        return "VARCHAR"


class RDPDDLCompiler(compiler.DDLCompiler):

    def visit_create_table(self, create):
        table = create.element
        preparer = self.preparer

        text = "\nCREATE "
        if table._prefixes:
            text += " ".join(table._prefixes) + " "
        text += "TABLE " + preparer.format_table(table) + " "

        create_table_suffix = self.create_table_suffix(table)
        if create_table_suffix:
            text += create_table_suffix + " "

        text += "("

        separator = "\n"

        # if only one primary key, specify it along with the column
        first_pk = False
        for create_column in create.columns:
            column = create_column.element
            try:
                processed = self.process(
                    create_column, first_pk=column.primary_key and not first_pk
                )
                if processed is not None:
                    text += separator
                    separator = ", \n"
                    text += "\t" + processed
                if column.primary_key:
                    first_pk = True
            except exc.CompileError as ce:
                util.raise_from_cause(
                    exc.CompileError(
                        util.u("(in table '%s', column '%s'): %s")
                        % (table.description, column.name, ce.args[0])
                    )
                )

        const = self.create_table_constraints(
            table,
            _include_foreign_key_constraints=create.include_foreign_key_constraints,  # noqa
        )
        if const:
            text += separator + "\t" + const

        text += "\n)%s" % self.post_create_table(table)
        return text

    # RDP do not support check constraint for boolean, and just return None here
    def visit_check_constraint(self, constraint):
        return None


class RDPExecutionContext(default.DefaultExecutionContext):
    pass


class RDPDialect(default.DefaultDialect):
    name = "rapidsdb"
    default_paramstyle = "format"

    statement_compiler = RDPStatementCompiler
    type_compiler = RDPTypeCompiler
    ddl_compiler = RDPDDLCompiler
    preparer: Type[RDPIdentifierPreparer] = RDPIdentifierPreparer
    execution_ctx_cls = RDPExecutionContext

    encoding = "utf-8"
    supports_statement_cache = True
    supports_native_boolean = True
    supports_alter = False
    supports_views = False
    convert_unicode = True
    supports_unicode_statements = True
    supports_unicode_binds = True
    requires_name_normalize = True

    postfetch_lastrowid = False
    supports_empty_insert = False
    supports_sane_rowcount = False
    supports_sane_multi_rowcount = False
    isolation_level = "REPEATABLE READ"
    supports_default_values = False
    supports_savepoints = False

    # A dictionary of TypeEngine classes from sqlalchemy.types mapped to subclasses that are specific to the dialect class
    colspecs = colspecs
    ischema_names = ischema_names
    type_map = type_map

    def __init__(self, isolation_level=None, auto_convert_lobs=True, **kwargs):
        super().__init__(**kwargs)
        self.isolation_level = isolation_level
        self.auto_convert_lobs = auto_convert_lobs
        self.identifier_preparer = self.preparer(self)
        self.default_schema_name = "SYSTEM"
        self.default_catalog_name = "RAPIDS"

    def create_connect_args(self, url: "URL") -> tuple:
        # create a dict from url options and change key 'username' to 'user'
        db_opts: dict = url.translate_connect_args(username="user")
        db_opts["user"] = db_opts["user"].upper()
        db_opts.setdefault("port", 4333)
        db_opts.update(url.query)
        meta_dict = self._parse_url(db_opts.setdefault("database", "RAPIDS/SYSTEM"))
        table_metadata = TableMetaData(meta_dict["catalog"], meta_dict["schema"])

        # kwargs.setdefault("federation", meta_dict["federation"])
        db_opts.setdefault("catalog", meta_dict["catalog"])
        db_opts.setdefault("schema", meta_dict["schema"])
        db_opts.setdefault("database", meta_dict["schema"])

        if table_metadata.get_catalog():
            self._set_default_catalog(table_metadata.get_catalog())
        if table_metadata.get_schema():
            self._set_default_schema(table_metadata.get_schema())

        return (), db_opts

    def _parse_url(self, db_url: str) -> dict:
        """Generate a dict of federation, catalog, schema names from db_url."""
        meta_dict: dict[str, Optional[str]] = {
            "federation": None,
            "catalog": None,
            "schema": None,
        }

        names = db_url.split("/")
        nums = len(names)
        if nums == 3:
            meta_dict["federation"] = names[0]
            meta_dict["catalog"] = names[1]
            meta_dict["schema"] = names[2]
        elif nums == 2:
            meta_dict["catalog"] = names[0]
            meta_dict["schema"] = names[1]
        elif nums == 1:
            meta_dict["catalog"] = meta_dict["schema"] = names[0]
        else:
            pass

        return meta_dict

    def on_connect(self):
        super_ = super().on_connect()

        def on_connect(conn):
            if super_ is not None:
                super_(conn)
            cursor = conn.cursor()
            cursor.close()

        return on_connect

    # _isolation_lookup = {
    #     "SERIALIZABLE",
    #     "READ UNCOMMITTED",
    #     "READ COMMITTED",
    #     "REPEATABLE READ",
    # }

    # does not work with pyrdpdb currently
    # def set_isolation_level(self, connection, level):
    #     if level == "AUTOCOMMIT":
    #         pass
    #     else:
    #         # no need to set autocommit false explicitly,since it is false by default
    #         if level not in self._isolation_lookup:
    #             raise exc.ArgumentError(
    #                 "Invalid value '%s' for isolation_level. "
    #                 "Valid isolation levels for %s are %s"
    #                 % (level, self.name, ", ".join(self._isolation_lookup))
    #             )
    #         else:
    #             pass

    # def get_isolation_level(self, connection):
    #     return self.isolation_level

    # Important ,but stil not know why TODO
    def _check_unicode_returns(self, connection):
        return True

    def _check_unicode_description(self, connection):
        return True

    # RDP need set a default schema for read and write data
    def _get_default_schema_name(self, connection):
        return self.default_schema_name

    def _set_default_schema(self, schema_name):
        self.default_schema_name = schema_name

    def _set_default_catalog(self, catalog_name):
        self.default_catalog_name = catalog_name

    def normalize_name(self, name):
        if name is None:
            return None

        if name.upper() == name and not self.identifier_preparer._requires_quotes(
            name.lower()
        ):
            name = name.lower()
        elif name.lower() == name:
            return quoted_name(name, quote=True)

        return name

    def denormalize_name(self, name):
        if name is None:
            return None

        if name.lower() == name and not self.identifier_preparer._requires_quotes(
            name.lower()
        ):
            name = name.upper()
        return name

    def has_table(self, connection, table_name, schema=None, **kw):
        """Return whether a specified table exists.

        Note: it is a synchronous function, requires sync connection.
        """
        # schema = schema or self.default_schema_name

        # how to make sure a table if exist in RDP ?
        qname = self._quote_string(table_name)
        # upper_table_name = qname.upper()
        if schema is not None:
            upper_schema = self._quote_string(schema.upper())

            result = connection.execute(
                satext(
                    "SELECT 1 FROM RAPIDS.SYSTEM.TABLES WHERE SCHEMA_NAME=%s AND TABLE_NAME=%s;"
                    % (upper_schema, qname)
                )
            )
        else:
            result = connection.execute(
                satext(
                    "SELECT 1 FROM RAPIDS.SYSTEM.TABLES WHERE TABLE_NAME=%s;" % (qname)
                )
            )

        table_exists = bool(result.first())
        return table_exists

    def has_sequence(self, connection, sequence_name, schema=None):
        """RDP do not support sequence"""
        return False

    @reflection.cache
    def get_schema_names(self, connection, **kwargs):
        """get all schemas of the db system"""
        result = connection.execute(
            satext("SELECT SCHEMA_NAME FROM RAPIDS.SYSTEM.SCHEMAS;")
        )

        return list([name for name, in result.fetchall()])

    @reflection.cache
    def get_table_names(self, connection, schema=None, **kwargs):
        """get all columns info of a specified schema"""
        schema = schema or self.default_schema_name
        schema = "'" + schema.upper() + "'"
        result = connection.execute(
            satext(
                f"SELECT TABLE_NAME FROM RAPIDS.SYSTEM.TABLES WHERE SCHEMA_NAME={schema};"
            )
        )

        tables = list(
            [
                # self.normalize_name(row[0]) for row in result.fetchall()
                row[0]
                for row in result.fetchall()
            ]
        )
        return tables

    def get_temp_table_names(self, connection, schema=None, **kwargs):
        """RDP do not support temp table"""
        return []

    def get_view_names(self, connection, schema=None, **kwargs):
        """RDP do not support view"""
        return []

    def get_view_definition(self, connection, view_name, schema=None, **kwargs):
        """RDP do not support view"""
        return ""

    @staticmethod
    def resolve_tablename(table_name) -> str:
        if table_name == table_name.lower():  # this is lowercase tablename
            query_table_name = table_name.upper()
        else:
            query_table_name = table_name
        return query_table_name

    @reflection.cache
    def get_columns(self, connection, table_name, schema=None, **kwargs):
        """get all columns info of a specified table"""

        schema = schema or self.default_schema_name
        table_name = self._quote_string(table_name)
        query_table_name = self.resolve_tablename(table_name)
        if schema is not None:
            schema = self._quote_string(schema).upper()
            result = connection.execute(
                satext(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, SCALE "
                    "FROM RAPIDS.SYSTEM.COLUMNS "
                    "WHERE SCHEMA_NAME=%s AND TABLE_NAME=%s ORDER BY ORDINAL;"
                    % (schema, query_table_name)
                )
            )
        else:
            result = connection.execute(
                satext(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, SCALE "
                    "FROM RAPIDS.SYSTEM.COLUMNS WHERE TABLE_NAME=%s ORDER BY ORDINAL;"
                    % (query_table_name)
                )
            )

        columns = []
        for row in result.fetchall():
            column = {"name": row[0], "nullable": row[2] == "TRUE"}
            # magic
            if hasattr(types, row[1]):
                if row[1] == "TIMESTAMP":
                    column["type"] = getattr(RDP_types, "DATETIME")
                else:
                    column["type"] = getattr(RDP_types, row[1])
            elif hasattr(RDP_types, row[1]):
                if row[1] == "TIMESTAMP":
                    column["type"] = getattr(types, "DATETIME")
                else:
                    column["type"] = getattr(types, row[1])
            else:
                util.warn(
                    "Did not recognize type '%s' of column '%s'"
                    % (row[1], column["name"])
                )
                column["type"] = types.NULLTYPE

            columns.append(column)
        # print(columns)
        return columns

    def get_multi_columns(self, connection, schema, filter_names, **kwargs):
        """Override default get_multi_columns to integrate with RapidsDB metadata retrival."""
        _schema = schema or self.default_schema_name
        result = {}

        table_filter = ""
        params = {"schema": _schema.upper()}
        metadata_query = (
            "SELECT SCHEMA_NAME, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, PRECISION, SCALE, COMMENT "
            "FROM RAPIDS.SYSTEM.COLUMNS "
            "WHERE SCHEMA_NAME = :schema {table_filter}"
        )
        if filter_names:
            table_filter = "AND TABLE_NAME IN :filter_names"
            query_filter_names = filter_names
            # query_filter_names = [self.resolve_tablename(n) for n in filter_names]
            params["filter_names"] = tuple(query_filter_names)
        stmt = metadata_query.format(table_filter=table_filter)
        rset = connection.execute(satext(stmt), params).fetchall()

        for row in rset:
            result_schema_name = row[0]  # for "SCHEMA_NAME"
            result_table_name = row[1]  # "TABLE_NAME"
            coltype = str_type_map.setdefault(row[3], sqltypes.NullType)  # 3: "DATA_TYPE"
            precision = int(row[5]) if row[5] else None
            scale = int(row[6]) if row[6] else None
            if coltype == sqltypes.NUMERIC:
                coltype = sqltypes.NUMERIC(precision, scale)
            elif coltype == sqltypes.DECIMAL:
                coltype = sqltypes.DECIMAL(precision, scale)
            cdict = {
                "name": row[2].lower(),
                "type": coltype,
                "nullable": bool(row[4]),
                "comment": row[7],
            }  # 2: "COLUMN_NAME", 4: "IS_NULLABLE"

            orig_tname = result_table_name
            key = (schema, result_table_name) if schema else (None, orig_tname)
            if key not in result:
                result[key] = []
            result[key].append(cdict)
        return result.items()

    def get_foreign_keys(self, connection, table_name, schema=None, **kwargs):
        """RDP do not support foreign keys"""
        return []

    def get_indexes(self, connection, table_name, schema=None, **kwargs):
        """get all indexes info of a specified table"""
        schema = schema or self.default_schema_name
        table_name = "'" + table_name + "'"

        if schema is not None:
            schema = "'" + schema + "'"
            result = connection.execute(
                satext(
                    "SELECT INDEX_NAME, IS_UNIQUE, COLUMN_NAME FROM  RAPIDS.SYSTEM.INDEXES WHERE SCHEMA_NAME=%s AND TABLE_NAME=%s ORDER BY ORDINAL;"
                    % (schema, table_name)
                )
            )
        else:
            result = connection.execute(
                satext(
                    "SELECT INDEX_NAME, IS_UNIQUE, COLUMN_NAME FROM  RAPIDS.SYSTEM.INDEXES WHERE TABLE_NAME=%s ORDER BY ORDINAL;"
                    % (table_name,)
                )
            )

        indexes = {}

        if result is not None:
            try:
                for row in result.fetchall():
                    name = row[0]
                    unique = row[1]
                    column = row[2]

                    name = self.normalize_name(name)
                    column = self.normalize_name(column)

                    if name not in indexes:
                        indexes[name] = {
                            "name": name,
                            "unique": unique,
                            "column_names": [column],
                        }
                    else:
                        indexes[name]["column_names"].append(column)
            except BaseException:
                print("Get indexe error.")

        return list(indexes.values())

    def get_pk_constraint(self, connection, table_name, schema=None, **kwargs):
        """RDP do not support constraint"""
        return []

    def get_unique_constraints(self, connection, table_name, schema=None, **kwargs):
        """RDP do not support unique constraints"""
        return []

    def get_check_constraints(self, connection, table_name, schema=None, **kwargs):
        """RDP do not support check constraints"""
        return []

    def get_table_oid(self, connection, table_name, schema=None, **kwargs):
        pass

    def get_table_comment(self, connection, table_name, schema=None, **kwargs):
        """RDP do not support table comment"""
        return {}

    def _quote_string(self, string) -> str:

        return "'" + string + "'"

    def do_savepoint(self, connection, name):
        """Require "SAVEPOINT" support from DB"""
        raise NotImplementedError("SAVEPOINT is not supported yet")

    def do_release_savepoint(self, connection, name):
        """Require "SAVEPOINT" support from DB"""
        raise NotImplementedError("SAVEPOINT is not supported yet")

    def do_rollback_to_savepoint(self, connection, name):
        """Require "SAVEPOINT" support from DB"""
        raise NotImplementedError("SAVEPOINT is not supported yet")


class TableMetaData(object):
    def __init__(self, catalog=None, schema=None, name=None):
        self.catalog = catalog
        self.schema = schema
        self.name = name

    def get_catalog(self):
        return self.catalog

    def get_schema(self):
        return self.schema

    def get_name(self):
        return self.name
