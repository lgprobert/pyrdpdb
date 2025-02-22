# pyrdpdb

Table of Contents

- Requirements
- Installation
- Documentation
- Example
- Resources
- License

pyrdpdb package is a Python DB-API 2.0 compliant driver package for RapidsDB database, which contains two pure-Python RapidsDB DB-API sub-packages: pyrdp and aiordp, based on PEP 249. Each driver itself also contains a SQLAlchemy dialect driver to allow seamless operations between SQLAlchemy and RapidsDB as a database source.

## Requirements

- Python: >= 3.9
- RapidsDB Server: >= 4.x

## Installation

Install package with `pip`:

```shell
python3 -m pip install pyrdpdb
```

## Documentation

## Example

```shell
# Demonstrate DB-API direct database connection
$ python -m pyrdpdb.pyrdp.example.dbapi <hostname>

$ python -m pyrdpdb.pyrdp.example.simple_sa <table_name> <hostname>

# assume RDP running on local host, use argument of either aiordp or pyrdp
$ python -m pyrdpdb.pyrdp.example.many [aiordp | pyrdp]

# Demonstrate DB-API direct database connection
$ python -m pyrdpdb.aiordp.example.engine <hostname>

$ python -m pyrdpdb.aiordp.example.simple_sa <hostname>

$ python -m pyrdpdb.aiordp.example.dbapi_cursor <hostname>

# assume RDP running on local host, use argument of either aiordp or pyrdp
$ python -m pyrdpdb.pyrdp.example.many [aiordp | pyrdp]
```

> Note: \<hostname> is optional, default to **localhost** if not provided.

## Resources

DB-API 2.0: <http://www.python.org/dev/peps/pep-0249>

## License

pyrdpdb is released under the MIT License. See LICENSE for more information.
