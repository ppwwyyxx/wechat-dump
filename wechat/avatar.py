#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: avatar.py
# Date: Wed Nov 29 03:27:16 2017 -0800
# Author: Yuxin Wu

from PIL import Image
import cStringIO
import glob
import os
import numpy as np
import logging
import sqlite3
logger = logging.getLogger(__name__)

from common.textutil import ensure_bin_str, md5


class AvatarReader(object):
    def __init__(self, res_dir, avt_db="avatar.index"):
        self.sfs_dir = os.path.join(res_dir, 'sfs')

        # new location of avatar, see #50
        self.avt_dir = os.path.join(res_dir, 'avatar')
        self.avt_db = avt_db
        self._use_avt = True
        if os.path.isdir(self.avt_dir) and len(os.listdir(self.avt_dir)):
            self.avt_use_db = False
        elif self.avt_db is not None \
                and os.path.isfile(self.avt_db) \
                and glob.glob(os.path.join(self.sfs_dir, 'avatar*')):
            self.avt_use_db = True
        else:
            logger.warn(
                    "Cannot find avatar files. Will not use avatar!")
            self._use_avt = False

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        if not self._use_avt:
            return None

        username = ensure_bin_str(username)
        filename = md5(username)
        dir1, dir2 = filename[:2], filename[2:4]
        filename = os.path.join(dir1, dir2,
                                "user_{}.png".format(filename))

        try:
            try:
                if self.avt_use_db:
                    pos, size = self.query_index(filename)
                    return self.read_img(pos, size)
                else:
                    img_file = os.path.join(self.avt_dir, filename)
                    if os.path.exists(img_file):
                        return Image.open(img_file)
                    else:
                        return None
            except TypeError:
                logger.warn("Avatar for {} not found in avatar database.".format(username))
                return None
        except Exception as e:
            raise
            print e
            logger.warn("Failed to retrieve avatar!")
            return None


    def read_img(self, pos, size):
        file_idx = pos >> 32
        fname = os.path.join(self.sfs_dir,
                'avatar.block.' + '{:05d}'.format(file_idx))
        # a 64-byte offset of each block file
        start_pos = pos - file_idx * (2**32) + 64
        try:
            with open(fname, 'rb') as f:
                f.seek(start_pos)
                data = f.read(size)
                im = Image.open(cStringIO.StringIO(data))
                return im
        except IOError as e:
            logger.warn("Cannot read avatar from {}: {}".format(fname, str(e)))
            return None

    def query_index(self, filename):
        conn = sqlite3.connect(self.avt_db)
        cursor = conn.execute("select Offset,Size from Index_avatar where FileName='{}'".format(filename))
        pos, size = cursor.fetchone()
        return pos, size
