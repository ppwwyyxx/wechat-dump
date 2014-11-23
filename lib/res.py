#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: res.py
# Date: Sun Nov 23 15:59:48 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import glob
import os
import Image
import cStringIO
import base64

from lib.avatar import AvatarReader

VOICE_DIRNAME = 'voice2'

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, res_dir):
        assert os.path.isdir(res_dir), "No such directory: {}".format(res_dir)
        self.res_dir = res_dir
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

    def get_avatar(self, username):
        """ return base64 string"""
        ret = self.avt_reader.get_avatar(username)
        if ret is None:
            return ""
        im = Image.fromarray(ret)
        buf = cStringIO.StringIO()
        im.save(buf, 'JPEG', quality=50)
        jpeg_str = buf.getvalue()
        return base64.b64encode(jpeg_str)



