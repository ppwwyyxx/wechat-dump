import os
from pathlib import Path
import logging
import tempfile
import io
import requests
import base64
import imghdr
from PIL import Image
import pickle
from Crypto.Cipher import AES

from .parser import WeChatDBParser
from .common.textutil import md5 as get_md5_hex, get_file_b64, get_file_md5


LIB_PATH = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EMOJI_CACHE = os.path.join(LIB_PATH, '..', 'emoji.cache')
logger = logging.getLogger(__name__)


def _get_aes_key(md5):
    # ascii representation of the first half of md5 is used as aes key
    assert len(md5) == 32
    return md5[:16].encode('ascii')
    # ret = ""
    # for ch in md5[:16]:
        # ret += format(ord(ch), 'x')
    # return ret


class EmojiReader:
    def __init__(self,
        resource_dir: str,
        parser: WeChatDBParser,
        cache_file: str=None):
        """
        Args:
            resource_dir: path to resource/
            parser: Database parser
            cache_file: a cache file to store emoji downloaded from URLs.
                default to a emoji.cache file under wechat-dump.
        """
        self.emoji_dir = Path(resource_dir) / 'emoji'
        assert self.emoji_dir.is_dir(), self.emoji_dir
        self.parser = parser
        self.emoji_info = parser.emoji_info or {}
        # mapping from md5 to the (cdnurl, encrypturl, aeskey)
        # columns in EmojiInfo table.
        self.cache_file = cache_file or DEFAULT_EMOJI_CACHE

        # cache stores md5 -> (base64str, format)
        if os.path.isfile(self.cache_file):
            with open(self.cache_file, "rb") as f:
                self._cache = pickle.load(f)
        else:
            self._cache = {}
        self._cache_size = len(self._cache)
        self.encryption_key = parser.get_emoji_encryption_key()
        if self.encryption_key is not None:
            self.encryption_key = _get_aes_key(self.encryption_key)

    def get_emoji(self, md5):
        """ Returns: (b64 encoded img string, format) """

        assert md5, f"Invalid md5 {md5}!"
        # check cache
        img, format = self._cache_query(md5)
        if format:
            return img, format

        # check resource/
        subdir = self.parser.emoji_groups.get(md5, '')
        dir_to_search = self.emoji_dir / subdir
        img, format = self._search_in_res(dir_to_search, md5, False)
        if format:
            return img, format

        emoji_info = self.emoji_info.get(md5, None)
        if emoji_info:
            catalog, cdnurl, encrypturl, aeskey = emoji_info
            img, format = self._fetch(md5, cdnurl, encrypturl, aeskey)
            if format:
                return img, format

        img, format = self._search_in_res(dir_to_search, md5, True)
        if format:
            logger.info(f"Using fallback for emoji {md5}")
            return img, format
        else:
            emoji_in_table = emoji_info is not None
            msg = "not in database" if not emoji_in_table else f"group='{subdir}'"
            logger.warning(f"Cannot find emoji {md5}: {msg}")
            return None, None

    def _cache_query(self, md5):
        data, format = self._cache.get(md5, (None, None))
        if data is not None and not isinstance(data, str):
            data = data.decode('ascii')
        return data, format

    def _cache_add(self, md5, values):
        self._cache[md5] = values
        if len(self._cache) >= self._cache_size + 15:
            self.flush_cache()

    def flush_cache(self):
        if len(self._cache) > self._cache_size:
            self._cache_size = len(self._cache)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self._cache, f, protocol=-1)

    def _search_in_res(self, dir, md5, allow_fallback=False):
        if allow_fallback:
            candidates = dir.glob(f'{md5}*')
            # There are misc low-quality matches, e.g.:
            # 'md5_{0..15}' for each frame of gif, non-animated md5_thumb, md5_cover
            # candidates = [k for k in candidates if not re.match('.*_[0-9]+$', k)]
            # candidates = [k for k in candidates if (not k.endswith('_cover') and not k.endswith('_thumb')))]
        else:
            if (dir / md5).is_file():
                candidates = [dir / md5]
            else:
                candidates = []

        def get_data_no_fallback(fname):
            if imghdr.what(fname):
                data_md5 = get_file_md5(fname)
                if data_md5 == md5:
                    return get_file_b64(fname), imghdr.what(fname)

            try:
                content = self._decode_emoji(fname)
                data_md5 = get_md5_hex(content)
                if data_md5 != md5:
                    if content.startswith(b"wxgf"):
                        raise ValueError("Unsupported mysterious image format: wxgf")
                    raise ValueError("Decoded data mismatch md5!")
                im = Image.open(io.BytesIO(content))
                return (base64.b64encode(content).decode('ascii'), im.format.lower())
            except Exception as e:
                logger.error(f"Error decoding emoji {fname} : {str(e)}")

        def get_data_fallback(fname):
            if not imghdr.what(fname):
                return  # fallback files are not encrypted
            return get_file_b64(fname), imghdr.what(fname)

        get_data_func = get_data_fallback if allow_fallback else get_data_no_fallback
        results = [(x, get_data_func(x)) for x in candidates]
        results = [(a, b) for a, b in results if b is not None]
        # maybe sort candidates by heuristics?
        if len(results):
            return results[0][1]
        return (None, None)

    def _decode_emoji(self, fname):
        cipher = AES.new(self.encryption_key, AES.MODE_ECB)
        with open(fname, 'rb') as f:
            head = f.read(1024)
            plain_head = cipher.decrypt(head)
            data = plain_head + f.read()
        return data

    def _fetch(self, md5, cdnurl, encrypturl, aeskey):
        ret = None
        if cdnurl:
            try:
                logger.info("Requesting emoji {} from {} ...".format(md5, cdnurl))
                r = requests.get(cdnurl).content
                emoji_md5 = get_md5_hex(r)
                im = Image.open(io.BytesIO(r))
                ret = (base64.b64encode(r).decode('ascii'), im.format.lower())
                if emoji_md5 == md5:
                    self._cache_add(md5, ret)
                    return ret
                else:
                    raise ValueError("Emoji MD5 from CDNURL does not match")
            except Exception:
                logger.debug("Error processing cdnurl {}".format(cdnurl))

        if encrypturl:
            try:
                logger.info("Requesting encrypted emoji {} from {} ...".format(md5, encrypturl))
                buf = requests.get(encrypturl).content
                aeskey = bytes.fromhex(aeskey)
                cipher = AES.new(aeskey, AES.MODE_CBC, iv=aeskey)
                decoded_buf = cipher.decrypt(buf)

                im = Image.open(io.BytesIO(decoded_buf))
                ret = (base64.b64encode(decoded_buf).decode('ascii'), im.format.lower())
                self._cache_add(md5, ret)
                return ret
            except Exception:
                logger.exception("Error processing encrypturl {}".format(encrypturl))
        if ret is not None:
            # ret may become something with wrong md5. Try it anyway, but don't cache.
            return ret
        return None, None

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    class Dummy():
        def _cache_add(self, md5, ret):
            pass
    # test decryption
    md5 = '5a7fc462d63ef845e6d99c1523bbc91e'
    encurl = 'http://emoji.qpic.cn/wx_emoji/CQmBgayyMuvscRVEKN9s4HyTjKVU9iacqqhyCpdtqOVcCql5JaibjDFg/'
    enckey = '8ba7f51f9f3ac58cf8ed937fc90200a6'
    b64, format = EmojiReader._fetch(Dummy(), md5, None, encurl, enckey)
    print("format=", format)
