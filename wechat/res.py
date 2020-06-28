# -*- coding: UTF-8 -*-

import glob
import os
import re
from PIL import Image
import tempfile
import io
import base64
import logging
logger = logging.getLogger(__name__)
import imghdr
from multiprocessing import Pool
import atexit
import pickle
import requests

from .avatar import AvatarReader
from .common.textutil import md5, get_file_b64
from .common.procutil import subproc_succ
from .common.timer import timing
from .msg import TYPE_SPEAK
from .audio import parse_wechat_audio_file

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
INTERNAL_EMOJI_DIR = os.path.join(LIB_PATH, 'static', 'internal_emoji')
VOICE_DIRNAME = 'voice2'
IMG_DIRNAME = 'image2'
EMOJI_DIRNAME = 'emoji'
VIDEO_DIRNAME = 'video'

JPEG_QUALITY = 50

class EmojiCache(object):
    def __init__(self, fname):
        self.fname = fname
        if os.path.isfile(fname):
            with open(fname, 'rb') as f:
                self.dic = pickle.load(f)
        else:
            self.dic = {}

        self._curr_size = len(self.dic)

    def query(self, md5):
        data, format = self.dic.get(md5, (None, None))
        if data is not None and not isinstance(data, str):
            data = data.decode('ascii')
        return data, format

    def fetch(self, md5, urls):
        cdnurl, encrypturl, aeskey = urls
        if cdnurl:
            try:
                logger.info("Requesting emoji {} from {} ...".format(md5, cdnurl))
                r = requests.get(cdnurl).content
                im = Image.open(io.BytesIO(r))
                ret = (base64.b64encode(r).decode('ascii'), im.format.lower())
                self.add(md5, ret)
                return ret
            except Exception:
                logger.exception("Error processing cdnurl {}".format(cdnurl))

        if encrypturl:
            try:
                logger.info("Requesting encrypted emoji {} from {} ...".format(md5, encrypturl))
                buf = requests.get(encrypturl).content
                with tempfile.TemporaryDirectory(prefix="wechat_dump_download") as d:
                    fname = os.path.join(d, md5)
                    with open(fname, 'wb') as f:
                        f.write(buf)
                    cmd = f"openssl enc -d -aes-128-cbc -in {fname} -K {aeskey} -iv {aeskey}"
                    decoded_buf = subproc_succ(cmd)
                im = Image.open(io.BytesIO(decoded_buf))
                ret = (base64.b64encode(decoded_buf).decode('ascii'), im.format.lower())
                self.add(md5, ret)
                return ret
            except Exception:
                logger.exception("Error processing encrypturl {}".format(encrypturl))
        return None, None

    def add(self, md5, values):
        self.dic[md5] = values
        if len(self.dic) >= self._curr_size + 10:
            self.flush()

    def flush(self):
        if len(self.dic) > self._curr_size:
            self._curr_size = len(self.dic)
            with open(self.fname, 'wb') as f:
                pickle.dump(self.dic, f)

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, parser, res_dir, avt_db):
        def check(subdir):
            dir_to_check = os.path.join(res_dir, subdir)
            assert os.path.isdir(dir_to_check), f"No such directory: {dir_to_check}"
        [check(k) for k in ['', IMG_DIRNAME, EMOJI_DIRNAME, VOICE_DIRNAME]]

        self.emoji_cache = EmojiCache(
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '..', 'emoji.cache'))
        self.res_dir = res_dir
        self.parser = parser
        self.voice_cache_idx = {}
        self.img_dir = os.path.join(res_dir, IMG_DIRNAME)
        self.voice_dir = os.path.join(res_dir, VOICE_DIRNAME)
        self.emoji_dir = os.path.join(res_dir, EMOJI_DIRNAME)
        self.video_dir = os.path.join(res_dir, VIDEO_DIRNAME)
        self.avt_reader = AvatarReader(res_dir, avt_db)

    def get_voice_filename(self, imgpath):
        fname = md5(imgpath.encode('ascii'))
        dir1, dir2 = fname[:2], fname[2:4]
        ret = os.path.join(self.voice_dir, dir1, dir2,
                           'msg_{}.amr'.format(imgpath))
        if not os.path.isfile(ret):
            logger.error("Voice file not found for {}".format(imgpath))
            return ""
        return ret

    def get_voice_mp3(self, imgpath):
        """ return mp3 and duration, or empty string and 0 on failure"""
        idx = self.voice_cache_idx.get(imgpath)
        if idx is None:
            return parse_wechat_audio_file(
                self.get_voice_filename(imgpath))
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
                                             (self.get_voice_filename(k),)) for k in voice_paths]

    def get_avatar(self, username):
        """ return base64 unicode string"""
        im = self.avt_reader.get_avatar(username)
        if im is None:
            logger.warning(f"Avatar for {username} is missing.")
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
            if not img_file.endswith('jpg') and \
               imghdr.what(img_file) != 'jpeg':
                im = Image.open(open(img_file, 'rb'))
                buf = io.BytesIO()
                im.convert('RGB').save(buf, 'JPEG', quality=JPEG_QUALITY)
                return base64.b64encode(buf.getvalue()).decode('ascii')
            return get_file_b64(img_file)

        big_file = get_jpg_b64(big_file)
        if big_file:
            return big_file
        return get_jpg_b64(small_file)

    def _get_res_emoji(self, md5, pack_id, allow_cover=False):
        """
        pack_id: can be None
        allow_cover: Cover is non-animated. Can be used as a fallback.
        """
        path = os.path.join(self.emoji_dir, pack_id or '')
        candidates = glob.glob(os.path.join(path, '{}*'.format(md5)))
        candidates = [k for k in candidates if not re.match('.*_[0-9]+$', k)]
        candidates = [k for k in candidates if (allow_cover or (not k.endswith('_cover') and not k.endswith('_thumb')))]

        for cand in candidates:
            if imghdr.what(cand):  # does not recognize
                return get_file_b64(cand), imghdr.what(cand)
        return None, None

    def _get_internal_emoji(self, fname):
        f = os.path.join(INTERNAL_EMOJI_DIR, fname)
        return get_file_b64(f), imghdr.what(f)

    def get_emoji_by_md5(self, md5):
        """ :returns: (b64 unicode img, format)"""
        assert md5, md5
        if md5 in self.parser.internal_emojis:
            emoji_img, format = self._get_internal_emoji(self.parser.internal_emojis[md5])
            return emoji_img, format
        else:
            # check cache
            img, format = self.emoji_cache.query(md5)
            if format:
                return img, format

            # check resource/emoji/ dir
            group = self.parser.emoji_groups.get(md5, None)
            emoji_img, format = self._get_res_emoji(md5, group)
            if format:
                return emoji_img, format

            # check url
            urls = self.parser.emoji_url.get(md5, None)
            if urls:
                emoji_img, format = self.emoji_cache.fetch(md5, urls)
                if format:
                    return emoji_img, format

            # check resource/emoji dir again, fallback to allow cover/thumbnail
            emoji_img, format = self._get_res_emoji(md5, group, allow_cover=True)
            if format:
                return emoji_img, format

            # TODO: first 1k in emoji is encrypted
            logger.warning("Cannot get emoji {} in group {}".format(md5, group))
            return None, None

    def get_video(self, videoid):
        video_file = os.path.join(self.video_dir, videoid + ".mp4")
        video_thumbnail_file = os.path.join(self.video_dir, videoid + ".jpg")
        if os.path.exists(video_file):
            return video_file
        elif os.path.exists(video_thumbnail_file):
            return video_thumbnail_file
        logger.warning(f"Cannot get video {videoid}")
        return ""
