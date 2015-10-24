<<<<<<< HEAD
import asyncio

import pytest


@pytest.fixture
def reader():
    return MockReader()


@pytest.fixture
def writer():
    return MockWriter()


@pytest.fixture
def patch_asyncio(monkeypatch, reader, writer):
    '''Fixture patches asyncio.open_connection to return a MockReader, MockWriter pair.'''

    @asyncio.coroutine
    def mock(*args, **kwargs):
        return reader, writer

    monkeypatch.setattr(asyncio, 'open_connection', mock)

    return None


class MockWriter:
    '''
    Mock implementation of asyncio.StreamWriter.

    Attributes:
        closed: A boolean indicating whether the transport protocol has been closed.
        written: A (possibly empty) list of bytes objects in the order that they were written to the transport.
    '''

    def __init__(self, *args, **kwargs):
        self.closed = False
        self.written = []

    def write(self, data):
        if self.closed:
            raise Exception('transport is closed')
        self.written.append(data)

    def close(self):
        self.closed = True


class MockReader:
    '''
    Mock implementation of asyncio.StreamReader.

    Attributes:
        buffer: A (possibly empty) list of bytes objects in the order that they are to be read.
        read: A (possibly empty) list of bytes objects in the order that they were read.
    '''

    def __init__(self, *args, **kwargs):
        self.buffer = []
        self.read = []

    @asyncio.coroutine
    def __aiter__(self):
        return self

    @asyncio.coroutine
    def __anext__(self):
        try:
            # this would be better done with deque.popleft, but self.buffer won't contain enough data to be beneficial
            val = self.buffer.pop(0)

        except IndexError:
            raise StopAsyncIteration

        self.read.append(val)

        return val
=======

>>>>>>> 7b02200f45383e1579d66f55e6ea6c4103885674
