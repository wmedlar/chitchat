import asyncio

import pytest
import pytest_asyncio

from chitchat.base import BaseClient


@pytest.fixture
def client(patch_asyncio):
    '''
    Fixture to return a new instance of BaseClient with asyncio.open_connection monkeypatched to return
    a pair of MockReader, MockWriter instances.
    '''
    return BaseClient(host='127.0.0.1', port=0)


def test_init_args():
    '''
    Test that the arguments passed to the BaseClient constructor are the arguments used as its attributes.
    '''
    HOST, PORT, SSL = '127.0.0.1', 0, True

    client = BaseClient(HOST, PORT, ssl=SSL)

    assert client.host is HOST
    assert client.port is PORT
    assert client.ssl is SSL


@pytest.mark.asyncio
def test_connect(client):
    '''
    Test that `connect` appropriately sets the `connected`, `reader`, and `writer` attributes, and triggers functions
    registered to the 'CONNECT' command.
    '''
    assert not client.connected
    assert not client.reader
    assert not client.writer

    yield from client.connect()

    assert client.connected
    assert client.reader
    assert client.writer

    raise NotImplementedError('CONNECT trigger has not been implemented')


@pytest.mark.asyncio
def test_connect_already_connected(client):
    '''
    Test that RuntimeError is raised when attempting to connect while already connected, and that no 'CONNECT' command
    is triggered by the failed attempt.
    '''
    yield from client.connect()

    with pytest.raises(RuntimeError):
        yield from client.connect()

    assert client.connected
    assert client.reader
    assert client.writer


@pytest.mark.asyncio
def test_change_host_port_ssl_while_connected(client):
    '''
    Test that AttributeErrors are raised while attempting to change any of the host, port, or ssl attributes while
    connected, and that the attributes are unaffected.
    '''
    yield from client.connect()

    HOST, PORT, SSL = client.host, client.port, client.ssl

    CHANGED = object()

    with pytest.raises(AttributeError):
        client.host = CHANGED

    assert client.host is HOST

    with pytest.raises(AttributeError):
        client.port = CHANGED

    assert client.port is PORT

    with pytest.raises(AttributeError):
        client.ssl = CHANGED

    assert client.ssl is SSL


@pytest.mark.asyncio
def test_disconnect(client):
    '''
    Test that `disconnect` appropriately unsets the `connected`, `reader`, and `writer` attributes, and triggers
    functions registered to the 'DISCONNECT' command.
    '''
    yield from client.connect()
    yield from client.disconnect()

    assert not client.connected
    assert not client.reader
    assert not client.writer

    raise NotImplementedError('DISCONNECT trigger has not been implemented')


@pytest.mark.asyncio
def test_disconnect_not_connected(client):
    '''
    Test that attempting to disconnect when not connected has no effect, and that no 'DISCONNECT' command is triggered
    by the failed attempt.
    '''
    yield from client.connect()
    yield from client.disconnect()

    yield from client.disconnect()

    raise NotImplementedError('DISCONNECT trigger has not been implemented')