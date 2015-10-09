#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: avatar.py
# Date: Thu Jun 18 00:02:07 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import numpy as np
import logging
import sqlite3
logger = logging.getLogger(__name__)

from common.textutil import ensure_bin_str, md5

class AvatarReader(object):
    def __init__(self, avt_dir, avt_db="avatar.index"):
        self.avt_dir = avt_dir
        self.avt_db = avt_db

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        username = ensure_bin_str(username)
        filename = md5(username)
        dir1, dir2 = filename[:2], filename[2:4]
        filename = os.path.join(dir1, dir2,
                                "user_{}.png.bm".format(filename))

        index_avatar = self.query_index(filename)
        if index_avatar == -1:
            logger.warn("Avatar not found for {}".format(username))
            return None
        else:
            img = self.read_bm_block(index_avatar)
            return img

    def read_bm_block(self, pos):
        file_idx = 0
        fname = os.path.join(self.avt_dir,
                'avatar.block.0000' + str(file_idx))
        with open(fname, 'rb') as f:
            start_pos = pos + 16 + 51
            # 51 = len('xx/xx/user_this-is-md5-of-length-32.png.bm\x00')
            f.seek(start_pos)
            size = (96, 96, 3)
            img = np.zeros(size, dtype='uint8')
            for i in range(96):
                for j in range(96):
                    r, g, b, a = map(ord, f.read(4))
                    img[i,j] = (r, g, b)
        return img

    def query_index(self, filename):
        conn = sqlite3.connect(self.avt_db)
        try:
            cursor = conn.execute("select Offset from Index_avatar where FileName='{}'".format(filename))
            index_avatar = cursor.fetchone()[0]
            return index_avatar
        except:
            return -1
