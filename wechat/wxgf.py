from websocket import create_connection
import os
import logging
import shutil
import subprocess


logger = logging.getLogger(__name__)

WXGF_HEADER = b'wxgf'
FAILURE_MESSAGE = b'FAILED'

_HEVC_START_CODE_4 = b"\x00\x00\x00\x01"
_HEVC_START_CODE_3 = b"\x00\x00\x01"


def extract_hevc_bitstream_from_wxgf(data: bytes) -> bytes | None:
    """Extract Annex-B HEVC bitstream from WXGF container.

    Returns:
        HEVC bitstream bytes starting with a start-code, or None if unknown format.
    """
    if not data.startswith(WXGF_HEADER):
        return None
    start = data.find(_HEVC_START_CODE_4)
    if start < 0:
        start = data.find(_HEVC_START_CODE_3)
    if start < 0:
        return None
    return data[start:]


def _subprocess_run_bytes(cmd: list[str], *, stdin: bytes) -> bytes | None:
    try:
        p = subprocess.run(
            cmd,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return None
    if p.returncode != 0:
        logger.debug(
            "Command failed (%s): rc=%d stderr=%s",
            " ".join(cmd),
            p.returncode,
            p.stderr[:2000].decode("utf-8", errors="replace"),
        )
        return None
    return p.stdout


def _ffprobe_count_frames_hevc(hevc: bytes, *, ffprobe: str = "ffprobe") -> int | None:
    out = _subprocess_run_bytes(
        [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=nw=1:nk=1",
            "-f",
            "hevc",
            "-i",
            "pipe:0",
        ],
        stdin=hevc,
    )
    if out is None:
        return None
    try:
        return int(out.strip().splitlines()[-1])
    except Exception:
        return None


def decode_wxgf_with_ffmpeg(
    data: bytes,
    *,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
) -> bytes | None:
    """Decode WXGF into a standard image/animation using ffmpeg.

    Returns:
        - PNG bytes for 1-frame WXGF
        - GIF bytes for multi-frame WXGF
        - None if decoding fails or ffmpeg/ffprobe is unavailable.
    """
    if shutil.which(ffmpeg) is None or shutil.which(ffprobe) is None:
        return None
    hevc = extract_hevc_bitstream_from_wxgf(data)
    if hevc is None:
        return None

    frames = _ffprobe_count_frames_hevc(hevc, ffprobe=ffprobe)
    if frames is not None and frames > 1:
        # Use palettegen/paletteuse for higher-quality gifs.
        out = _subprocess_run_bytes(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "hevc",
                "-i",
                "pipe:0",
                "-filter_complex",
                "[0:v]split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop",
                "0",
                "-f",
                "gif",
                "-",
            ],
            stdin=hevc,
        )
        if out is not None:
            return out

    # Default: decode the first frame to PNG (keeps quality and alpha).
    return _subprocess_run_bytes(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "hevc",
            "-i",
            "pipe:0",
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ],
        stdin=hevc,
    )


class WxgfAndroidDecoder:

    def __init__(self, server: str | None):
        """server: hostname:port"""
        if server is not None:
            if "://" not in server:
                server = "ws://" + server
            logger.info(f"Connecting to {server} ...")
            self.server = server
            self.ws = create_connection(server)

    def __del__(self):
        if self.has_server():
            self.ws.close()

    def has_server(self) -> bool:
        return hasattr(self, 'ws')

    def decode(self, data: bytes) -> bytes | None:
        assert data[:4] == WXGF_HEADER, data[:20]
        try:
            self.ws.send(data, opcode=0x2)
        except BrokenPipeError as e:
            logger.warning(f'Failed to send data to wxgf service. {e}. Reconnecting ..')
            self.ws = create_connection(self.server)
            self.ws.send(data, opcode=0x2)
        try:
            res = self.ws.recv()
        except Exception as e:
            logger.warning(f'Failed to recv data to wxgf service. {e}. Reconnecting ..')
            self.ws = create_connection(self.server)
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

        # Prefer host-side decoding via ffmpeg to avoid Android dependencies.
        res = decode_wxgf_with_ffmpeg(data)
        if res is None and self.has_server():
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
