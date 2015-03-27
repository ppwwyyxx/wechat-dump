#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: res.py
# Date: Fri Mar 27 23:42:16 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import glob
import os
import re
# TODO: perhaps we don't need to introduce PIL and numpy. libjpeg might be enough
from PIL import Image
import cStringIO
import base64
import logging
logger = logging.getLogger(__name__)
import imghdr
from multiprocessing import Pool

import pysox

from .avatar import AvatarReader
from .utils import timing, md5, get_file_b64
from .msg import TYPE_SPEAK

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
INTERNAL_EMOJI_DIR = os.path.join(LIB_PATH, 'static', 'internal_emoji')
VOICE_DIRNAME = 'voice2'
IMG_DIRNAME = 'image2'
EMOJI_DIRNAME = 'emoji'
AVATAR_DIRNAME = 'avatar'

JPEG_QUALITY = 50

def do_get_voice_mp3(amr_fpath):
    """ return base64 string, and voice duration"""
    if not amr_fpath: return "", 0
    mp3_file = os.path.join('/tmp',
                            os.path.basename(amr_fpath)[:-4] + '.mp3')

    infile = pysox.CSoxStream(amr_fpath)
    outfile = pysox.CSoxStream(mp3_file, 'w', infile.get_signal())
    chain = pysox.CEffectsChain(infile, outfile)
    chain.flow_effects()
    outfile.close()

    signal = infile.get_signal().get_signalinfo()
    duration = signal['length'] * 1.0 / signal['rate']
    mp3_string = get_file_b64(mp3_file)
    os.unlink(mp3_file)
    return mp3_string, duration

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, res_dir):
        def check(subdir):
            assert os.path.isdir(os.path.join(res_dir, subdir)), \
                    "No such directory: {}".format(subdir)
        [check(k) for k in ['', AVATAR_DIRNAME, IMG_DIRNAME, EMOJI_DIRNAME, VOICE_DIRNAME]]

        self.res_dir = res_dir
        self.voice_cache_idx = {}
        self.img_dir = os.path.join(res_dir, IMG_DIRNAME)
        self.voice_dir = os.path.join(res_dir, VOICE_DIRNAME)
        self.emoji_dir = os.path.join(res_dir, EMOJI_DIRNAME)
        self.avt_reader = AvatarReader(os.path.join(res_dir, AVATAR_DIRNAME))

    def get_voice_filename(self, imgpath):
        fname = md5(imgpath)
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
            return do_get_voice_mp3(
                self.get_voice_filename(imgpath))
        return self.voice_cache[idx].get()

    def cache_voice_mp3(self, msgs):
        """ for speed.
        msgs: a collection of WeChatMsg, to cache for later fetch"""
        voice_paths = [msg.imgPath for msg in msgs if msg.type == TYPE_SPEAK]
        self.voice_cache_idx = {k: idx for idx, k in enumerate(voice_paths)}
        pool = Pool(3)
        self.voice_cache = [pool.apply_async(do_get_voice_mp3,
                                             (self.get_voice_filename(k),)) for k in voice_paths]

    def get_avatar(self, username):
        """ return base64 string"""
        ret = self.avt_reader.get_avatar(username)
        if ret is None:
            return ""
        im = Image.fromarray(ret)
        buf = cStringIO.StringIO()
        im.save(buf, 'JPEG', quality=JPEG_QUALITY)
        jpeg_str = buf.getvalue()
        return base64.b64encode(jpeg_str)

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
        ths = filter(name_is_thumbnail, [k[0] for k in cands])
        if not ths:
            return (big[0], "")
        return (big[0], ths[0])


    def get_img(self, fnames):
        """ return two base64 jpg string"""
        fnames = [k for k in fnames if k]   # filter out empty string
        big_file, small_file = self._get_img_file(fnames)

        def get_jpg_b64(img_file):
            if not img_file:
                return None
            if not img_file.endswith('jpg') and \
               imghdr.what(img_file) != 'jpeg':
                im = Image.open(open(img_file, 'rb'))
                buf = cStringIO.StringIO()
                im.save(buf, 'JPEG', quality=JPEG_QUALITY)
                return base64.b64encode(buf.getvalue())
            return get_file_b64(img_file)
        big_file = get_jpg_b64(big_file)
        if big_file:
            return big_file
        return get_jpg_b64(small_file)

    def get_emoji(self, md5, pack_id):
        path = self.emoji_dir
        if pack_id:
            path = os.path.join(path, pack_id)
        candidates = glob.glob(os.path.join(path, '{}*'.format(md5)))
        candidates = [k for k in candidates if \
                      not k.endswith('_thumb') and not k.endswith('_cover')]
        if len(candidates) > 1:
            # annimation
            candidates = [k for k in candidates if not re.match('.*_[0-9]+$', k)]
            # only one file is the gif in need, others are frames or cover
            if len(candidates) == 0:
                # TODO stitch frames to gif
                logger.warning("Cannot find emoji: {}".format(md5))
                return None, None
        if not candidates:
            return None, None
        fname = candidates[0]
        return get_file_b64(fname), imghdr.what(fname)

    def get_internal_emoji(self, fname):
        f = os.path.join(INTERNAL_EMOJI_DIR, fname)
        return get_file_b64(f), imghdr.what(f)


