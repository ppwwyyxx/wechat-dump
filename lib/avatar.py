#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: avatar.py
# Date: Sun Nov 23 16:28:00 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import md5
import numpy as np

from .utils import ensure_bin_str

class AvatarReader(object):
    def __init__(self, res_dir):
        self.avt_dir = os.path.join(res_dir, 'avatar')
        assert os.path.isdir(self.avt_dir), "No such directory {}".format(self.avt_dir)

    @staticmethod
    def get_filename(username):
        m = md5.new()
        m.update(username)
        return m.hexdigest()

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        username = ensure_bin_str(username)
        filename = AvatarReader.get_filename(username)
        dir1, dir2 = filename[:2], filename[2:4]
        filename = os.path.join(self.avt_dir, dir1, dir2,
                                "user_{}.png.bm".format(filename))
        if not os.path.isfile(filename):
            # avatar not found!
            return None
        else:
            return AvatarReader.read_bm(filename)

    @staticmethod
    def read_bm(fname):
        size = (96, 96, 3)
        img = np.zeros(size, dtype='uint8')
        with open(fname, 'rb') as f:
            for i in range(96):
                for j in range(96):
                    r, g, b, a = map(ord, f.read(4))
                    img[i,j] = (r, g, b)
        return img
