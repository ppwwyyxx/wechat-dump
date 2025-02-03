from websocket import create_connection
import os
import logging


logger = logging.getLogger(__name__)

WXGF_HEADER = b'wxgf'
FAILURE_MESSAGE = b'FAILED'


class WxgfAndroidDecoder:

    def __init__(self, server: str | None):
        """server: hostname:port"""
        if server is not None:
            if "://" not in server:
                server = "ws://" + server
            logger.info(f"Connecting to {server} ...")
            self.ws = create_connection(server)

    def __del__(self):
        if self.has_server():
            self.ws.close()

    def has_server(self) -> bool:
        return hasattr(self, 'ws')

    def decode(self, data: bytes) -> bytes | None:
        assert data[:4] == WXGF_HEADER, data[:20]
        self.ws.send(data, opcode=0x2)
        res = self.ws.recv()
        if res == FAILURE_MESSAGE:
            return None
        return res

    def decode_with_cache(self, fname: str, data: bytes | None) -> bytes | None:
        """Decode and save cache.

        Args:
            fname: original file path. cache will be saved alongside.
            data: data to decode. None to use content of fname.
        """
        if data is None:
            with open(fname, 'rb') as f:
                data = f.read()
        out_fname = os.path.splitext(fname)[0] + '.dec'

        if os.path.exists(out_fname):
            with open(out_fname, 'rb') as f:
                return f.read()

        if not self.has_server():
            return None
        res = self.decode(data)

        if res is not None:
            with open(out_fname, 'wb') as f:
                f.write(res)
        return res


def is_wxgf_file(fname):
    with open(fname, 'rb') as f:
        return f.read(4) == WXGF_HEADER

def is_wxgf_buffer(buf: bytes):
    return buf[:4] == WXGF_HEADER
