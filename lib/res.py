#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: res.py
# Date: Sun Nov 23 21:08:44 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import glob
import os
import Image
import cStringIO
import base64

from lib.avatar import AvatarReader

VOICE_DIRNAME = 'voice2'
JPEG_QUALITY = 50

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, res_dir):
        assert os.path.isdir(res_dir), "No such directory: {}".format(res_dir)
        self.res_dir = res_dir
        self.img_dir = os.path.join(res_dir, 'image2')
        self.avt_reader = AvatarReader(self.res_dir)
        self.init()

    def init(self):
        """ load some index in memory"""
        self.speak_data = {}
        for root, subdirs, files in os.walk(
            os.path.join(self.res_dir, VOICE_DIRNAME)):
            if subdirs:
                continue
            for f in files:
                if not f.endswith('amr'):
                    continue
                full_path = os.path.join(root, f)
                key = f[4:-4]  # msg_xxxxx.amr
                assert len(key) == 26, \
                    "Error interpreting the protocol, this is a bug!"
                self.speak_data[key] = full_path

    @staticmethod
    def get_file_b64(fname):
        data = open(fname, 'rb').read()
        return base64.b64encode(data)

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

    def get_img_file(self, fname, smart):
        """ return base64 string"""
        dir1, dir2 = fname[:2], fname[2:4]
        if not smart:
            filename = os.path.join(self.img_dir, dir1, dir2, fname)
            if os.path.isfile(filename):
                return filename
        else:
            dirname = os.path.join(self.img_dir, dir1, dir2)
            if not os.path.isdir(dirname):
                print "Directory not found: {}".format(dirname)
                return ""
            maxf, maxsize = "", 0
            for f in os.listdir(dirname):
                if fname in f:
                    full_name = os.path.join(dirname, f)
                    size = os.path.getsize(full_name)
                    if size > maxsize:
                        maxsize = size
                        maxf = full_name
            if maxsize == 0:
                return ""
            else:
                return maxf
        return ""

    def get_img(self, fname, smart=True):
        img_file = self.get_img_file(fname, smart)
        if not img_file.endswith('jpg') or not img_file.startswith('th_'):
            im = Image.open(open(img_file, 'rb'))
            buf = cStringIO.StringIO()
            im.save(buf, 'JPEG', quality=JPEG_QUALITY)
            return base64.b64encode(buf.getvalue())
        else:
            return Resource.get_file_b64(img_file)
