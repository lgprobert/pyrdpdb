# SQLAlchemy dialect for RDP

This dialect allows you to use the RDP database with SQLAlchemy. It can use the supported RDP Python Driver pyrdpdb.

## Prerequisites
Python >=3.6 with installed pyrdpdb DBAPI implementation.

RDPClient Python Driver see RDPClient Interface Programming Reference or the install section of pyrdpdb.

## Install
Install from Python Package Index:

$ pip install sqlalchemy-RDP

## Getting started

After installation of sqlalchemy-RDP, you can create a engine which connects to a RDP instance. This engine works like all other engines of SQLAlchemy.

from sqlalchemy import create_engine
engine = create_engine('RDP://username:password@example.de:4333/federation/catalog/schema')
