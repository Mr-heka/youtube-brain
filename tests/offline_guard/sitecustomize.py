"""Block Python socket access while the bundled offline test suite runs."""
import socket


def _blocked(*_args, **_kwargs):
    raise RuntimeError("network disabled by topic-brain-builder offline smoke")


class _OfflineSocket(socket.socket):
    def connect(self, *_args, **_kwargs):
        return _blocked()

    def connect_ex(self, *_args, **_kwargs):
        return _blocked()


socket.socket = _OfflineSocket
socket.create_connection = _blocked
socket.getaddrinfo = _blocked
