import abc
import asyncio
import types


class AbstractConnection(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, host, port, *, ssl=True):
        pass

    @abc.abstractproperty
    def connected(self):
        pass

    @asyncio.coroutine
    @abc.abstractmethod
    def connect(self):
        pass

    @asyncio.coroutine
    @abc.abstractmethod
    def disconnect(self):
        pass


class Connection(AbstractConnection):


    def __init__(self, host, port, *, ssl=True):
        self._host = host
        self._port = port
        self._ssl = ssl
        self._connected = False

        self.reader = None
        self.writer = None


    @property
    def host(self):
        return self._host


    @host.setter
    def host(self, value):

        if self.connected:
            raise AttributeError("can't modify host while connected")

        self._host = value


    @property
    def port(self):
        return self._port


    @port.setter
    def port(self, value):

        if self.connected:
            raise AttributeError("can't modify port while connected")

        self._port = value


    @property
    def ssl(self):
        return self._ssl


    @ssl.setter
    def ssl(self, value):

        if self.connected:
            raise AttributeError("can't modify ssl while connected")

        self._ssl = value


    @property
    def connected(self):
        return self._connected


    @asyncio.coroutine
    def connect(self):

        if self.connected:
            raise RuntimeError('connection to {0.host!r} already opened on port {0.port}'.format(self))

        self.reader, self.writer = yield from asyncio.open_connection(self.host, self.port, ssl=self.ssl)
        self._connected = True

        yield


    @asyncio.coroutine
    def disconnect(self):

        if not self.connected:
            return

        self.reader = None
        self.writer.close()
        self.writer = None

        self._connected = False

        yield


    # must be a types.coroutine, not asyncio.coroutine
    @types.coroutine
    def send(self, message):

        if not self.writer:
            raise RuntimeError

        return self.writer.write(message)