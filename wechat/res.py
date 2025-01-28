# -*- coding: UTF-8 -*-

import os
from PIL import Image
import time
import io
import base64
import logging
logger = logging.getLogger(__name__)
import imghdr
from multiprocessing import Pool
import atexit

from .emoji import EmojiReader
from .avatar import AvatarReader
from .common.textutil import md5 as get_md5_hex, get_file_b64
from .msg import TYPE_SPEAK
from .audio import parse_wechat_audio_file
from .wxgf import WxgfAndroidDecoder, is_wxgf_file

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
VOICE_DIRNAME = 'voice2'
IMG_DIRNAME = 'image2'
EMOJI_DIRNAME = 'emoji'
VIDEO_DIRNAME = 'video'

JPEG_QUALITY = 50

class Resource(object):
    """ Multimedia resources parser."""
    def __init__(self, parser,
                 res_dir: str,
                 *,
                 wxgf_server: str | None = None,
                 avt_db: str | None = None):
        """
        Args:
            res_dir: path to the resource directory
            wxgf_server: "hostname:port" that points to the wxgf converter android app
            avt_db: "avatar.index" file that only exists in old versions of wechat
        """
        def check(subdir):
            dir_to_check = os.path.join(res_dir, subdir)
            assert os.path.isdir(dir_to_check), f"No such directory: {dir_to_check}"
        [check(k) for k in ['', IMG_DIRNAME, EMOJI_DIRNAME, VOICE_DIRNAME]]

        self.res_dir = res_dir
        self.parser = parser
        self.voice_cache_idx = {}
        self.img_dir = os.path.join(res_dir, IMG_DIRNAME)
        self.voice_dir = os.path.join(res_dir, VOICE_DIRNAME)
        self.video_dir = os.path.join(res_dir, VIDEO_DIRNAME)
        self.avt_reader = AvatarReader(res_dir, avt_db)
        self.wxgf_decoder = WxgfAndroidDecoder(wxgf_server)
        self.emoji_reader = EmojiReader(res_dir, self.parser)

    def _get_voice_filename(self, imgpath):
        fname = get_md5_hex(imgpath.encode('ascii'))
        dir1, dir2 = fname[:2], fname[2:4]
        ret = os.path.join(self.voice_dir, dir1, dir2,
                           'msg_{}.amr'.format(imgpath))
        if not os.path.isfile(ret):
            logger.error(f"Cannot find voice file {imgpath}, {fname}")
            return ""
        return ret

    def get_voice_mp3(self, imgpath):
        """ return mp3 and duration, or empty string and 0 on failure"""
        idx = self.voice_cache_idx.get(imgpath)
        if idx is None:
            return parse_wechat_audio_file(
                self._get_voice_filename(imgpath))
        return self.voice_cache[idx].get()

    def cache_voice_mp3(self, msgs):
        """ for speed.
        msgs: a collection of WeChatMsg, to cache for later fetch"""
        voice_paths = [msg.imgPath for msg in msgs if msg.type == TYPE_SPEAK]
        # NOTE: remove all the caching code to debug serial decoding
        self.voice_cache_idx = {k: idx for idx, k in enumerate(voice_paths)}
        pool = Pool(3)
        atexit.register(lambda x: x.terminate(), pool)
        self.voice_cache = [pool.apply_async(parse_wechat_audio_file,
                                             (self._get_voice_filename(k),)) for k in voice_paths]

    def get_avatar(self, username):
        """ return base64 unicode string"""
        im = self.avt_reader.get_avatar(username)
        if im is None:
            logger.warning(f"Cannot find avatar for {username}.")
            return ""
        buf = io.BytesIO()
        try:
            im.save(buf, 'JPEG', quality=JPEG_QUALITY)
        except IOError:
            try:
                # sometimes it works the second time...
                im.save(buf, 'JPEG', quality=JPEG_QUALITY)
            except IOError:
                return ""
        jpeg_str = buf.getvalue()
        return base64.b64encode(jpeg_str).decode('ascii')

    def _get_img_file(self, fnames):
        """ fnames: a list of filename to search for
            return (filename, filename) of (big, small) image.
            could be empty string.
        """
        cands = []
        for fname in fnames:
            dir1, dir2 = fname[:2], fname[2:4]
            dirname = os.path.join(self.img_dir, dir1, dir2)
            if not os.path.isdir(dirname):
                logger.warn("Directory not found: {}".format(dirname))
                continue
            for f in os.listdir(dirname):
                if fname in f:
                    full_name = os.path.join(dirname, f)
                    size = os.path.getsize(full_name)
                    if size > 0:
                        cands.append((full_name, size))
        if not cands:
            return ("", "")
        cands = sorted(cands, key=lambda x: x[1])

        def name_is_thumbnail(name):
            return os.path.basename(name).startswith('th_') \
                    and not name.endswith('hd')
        if len(cands) == 1:
            name = cands[0][0]
            if name_is_thumbnail(name):
                # thumbnail
                return ("", name)
            else:
                logger.warn("Found big image but not thumbnail: {}".format(fname))
                return (name, "")
        big = cands[-1]
        ths = list(filter(name_is_thumbnail, [k[0] for k in cands]))
        if not ths:
            return (big[0], "")
        return (big[0], ths[0])

    def get_img(self, fnames):
        """
        :params fnames: possible file paths
        :returns: two base64 jpg string
        """
        fnames = [k for k in fnames if k]   # filter out empty string
        big_file, small_file = self._get_img_file(fnames)

        def get_jpg_b64(img_file):
            if not img_file:
                return None

            # True jpeg. Simplest case.
            if img_file.endswith('jpg') and \
                   imghdr.what(img_file) == 'jpeg':
                return get_file_b64(img_file)

            if is_wxgf_file(img_file):
                start = time.time()
                buf = self.wxgf_decoder.decode_with_cache(img_file, None)
                if buf is None:
                    if not self.wxgf_decoder.has_server():
                        logger.warning("wxgf decoder server is not provided. Cannot decode wxgf images. Please follow instructions to create wxgf decoder server if these images need to be decoded.")
                    else:
                        logger.error("Failed to decode wxgf file: {}".format(img_file))
                    return None
                else:
                    elapsed = time.time() - start
                    if elapsed > 0.01 and self.wxgf_decoder.has_server():
                        logger.info(f"Decoded {img_file} in {elapsed:.2f} seconds")
            else:
                with open(img_file, 'rb') as f:
                    buf = f.read()

            # File is not actually jpeg. Convert.
            if imghdr.what(file=None, h=buf) != 'jpeg':
                try:
                    im = Image.open(io.BytesIO(buf))
                except:
                    return None
                else:
                    bufio = io.BytesIO()
                    im.convert('RGB').save(bufio, 'JPEG', quality=JPEG_QUALITY)
                    buf = bufio.getvalue()
            return base64.b64encode(buf).decode('ascii')

        big_file = get_jpg_b64(big_file)
        if big_file:
            return big_file
        return get_jpg_b64(small_file)

    def get_emoji_by_md5(self, md5):
        """ Returns: (b64 encoded img string, format) """
        return self.emoji_reader.get_emoji(md5)

    def get_video(self, videoid):
        video_file = os.path.join(self.video_dir, videoid + ".mp4")
        video_thumbnail_file = os.path.join(self.video_dir, videoid + ".jpg")
        if os.path.exists(video_file):
            return video_file
        elif os.path.exists(video_thumbnail_file):
            return video_thumbnail_file
        logger.warning(f"Cannot find video {videoid}")
        return ""
