#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: avatar.py
# Date: Fri Jan 09 22:21:55 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import numpy as np

from .utils import ensure_bin_str, md5

class AvatarReader(object):
    def __init__(self, res_dir):
        self.avt_dir = os.path.join(res_dir, 'avatar')
        assert os.path.isdir(self.avt_dir), \
            "No such directory {}".format(self.avt_dir)

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        username = ensure_bin_str(username)
        filename = md5(username)
        dir1, dir2 = filename[:2], filename[2:4]
        filename = os.path.join(self.avt_dir, dir1, dir2,
                                "user_{}.png.bm".format(filename))
        if not os.path.isfile(filename):
            # avatar not found!
            return None
        else:
            img = AvatarReader.read_bm(filename)
            return img

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
