# -*- coding: utf-8 -*-
import struct
import time
from functools import wraps
from collections.abc import Coroutine

import logging

logger = logging.getLogger("pyrdp.utils")


def timeit(func):
    """Decorator to time function execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        results = func(*args, **kwargs)
        end_time = time.time()
        runtime = round((end_time - start_time), 4)
        print(f"{runtime:.4f} seconds.")

        return results

    return wrapper


def int2_4bytes(i):
    """
    Encode int to 4 bytes.
    :param number i : input int .
    :return : 4 bytes
    """
    return struct.pack(">I", i)


def bytes2int(bs):
    """
    Decode bytes to int.
    :param bytes bs : input bytes .
    :return : int
    """
    return struct.unpack(">I", bs)


def int2byte(i):
    """
    Encode int to byte.
    :param number i : input int .
    :return : byte
    """
    return struct.pack("!B", i)


def byte2int(b):
    """
    Decode byte to int.
    :param byte b : input byte .
    :return : int
    """
    if isinstance(b, int):
        return b
    else:
        return struct.unpack("!B", b)[0]


def join_bytes(bs):
    if len(bs) == 0:
        return ""
    else:
        rv = bs[0]
        for b in bs[1:]:
            rv += b
        return rv


def _pack_int24(n):
    return struct.pack("<I", n)[:3]


def _lenenc_int(i):
    if i < 0:
        raise ValueError(
            "Encoding %d is less than 0 - no representation in LengthEncodedInteger" % i
        )
    elif i < 0xFB:
        return bytes([i])
    elif i < (1 << 16):
        return b"\xfc" + struct.pack("<H", i)
    elif i < (1 << 24):
        return b"\xfd" + struct.pack("<I", i)[:3]
    elif i < (1 << 64):
        return b"\xfe" + struct.pack("<Q", i)
    else:
        raise ValueError(
            "Encoding %x is larger than %x - no representation in LengthEncodedInteger"
            % (i, (1 << 64))
        )


class _ContextManager(Coroutine):

    __slots__ = ("_coro", "_obj")

    def __init__(self, coro):
        self._coro = coro
        self._obj = None

    def send(self, value):
        return self._coro.send(value)

    def throw(self, typ, val=None, tb=None):
        if val is None:
            return self._coro.throw(typ)
        elif tb is None:
            return self._coro.throw(typ, val)
        else:
            return self._coro.throw(typ, val, tb)

    def close(self):
        return self._coro.close()

    @property
    def gi_frame(self):
        return self._coro.gi_frame

    @property
    def gi_running(self):
        return self._coro.gi_running

    @property
    def gi_code(self):
        return self._coro.gi_code

    def __next__(self):
        return self.send(None)

    def __iter__(self):
        return self._coro.__await__()

    def __await__(self):
        return self._coro.__await__()

    async def __aenter__(self):
        self._obj = await self._coro
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        await self._obj.close()
        self._obj = None


class _ConnectionContextManager(_ContextManager):
    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._obj.close()
        else:
            await self._obj.ensure_closed()
        self._obj = None


class _PoolContextManager(_ContextManager):
    async def __aexit__(self, exc_type, exc, tb):
        self._obj.close()
        await self._obj.wait_closed()
        self._obj = None


class _SAConnectionContextManager(_ContextManager):
    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._obj is None:
            self._obj = await self._coro

        try:
            return await self._obj.__anext__()
        except StopAsyncIteration:
            await self._obj.close()
            self._obj = None
            raise


class _TransactionContextManager(_ContextManager):
    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            # await self._obj.rollback()
            pass
        else:
            if self._obj.is_active:
                # await self._obj.commit()
                pass
        self._obj = None


class _PoolAcquireContextManager(_ContextManager):

    __slots__ = ("_coro", "_conn", "_pool")

    def __init__(self, coro, pool):
        self._coro = coro
        self._conn = None
        self._pool = pool

    async def __aenter__(self):
        logger.info("Entering context, acquiring connection...")
        self._conn = await self._coro
        logger.debug("Connection acquired:", self._conn)
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self._pool.release(self._conn)
        finally:
            self._pool = None
            self._conn = None


class _PoolConnectionContextManager:
    """Context manager.

    This enables the following idiom for acquiring and releasing a
    connection around a block:

        with (yield from pool) as conn:
            cur = yield from conn.cursor()

    while failing loudly when accidentally using:

        with pool:
            <block>
    """

    __slots__ = ("_pool", "_conn")

    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def __enter__(self):
        assert self._conn
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._pool.release(self._conn)
        finally:
            self._pool = None
            self._conn = None

    async def __aenter__(self):
        assert not self._conn
        self._conn = await self._pool.acquire()
        return self._conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self._pool.release(self._conn)
        finally:
            self._pool = None
            self._conn = None
