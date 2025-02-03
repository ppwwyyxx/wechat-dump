#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from PIL import Image
import io
import glob
import os
import numpy as np
import logging
import sqlite3
logger = logging.getLogger(__name__)

from .common.textutil import md5


def _filename_priority(s):
    if "_hd" in s and s.endswith(".png"):
        return 10
    else:
        return 1


class AvatarReader(object):
    def __init__(self, res_dir, avt_db="avatar.index"):
        self.sfs_dir = os.path.join(res_dir, 'sfs')

        # new location of avatar, see #50
        self.avt_dir = os.path.join(res_dir, 'avatar')
        if not os.path.isdir(self.avt_dir) or len(os.listdir(self.avt_dir)) == 0:
            self.avt_dir = None

        self.avt_db = avt_db
        self._use_avt = True
        if self.avt_db is not None:
            if len(glob.glob(os.path.join(self.sfs_dir, 'avatar*'))) == 0:
                # has sfs/avatar*
                self.avt_db = None
        if self.avt_dir is None and self.avt_db is None:
            logger.warn("Cannot find avatar storage. Will not use avatar!")
            self._use_avt = False

    def get_avatar_from_avtdb(self, avtid):
        try:
            candidates = self._search_avt_db(avtid)
            candidates = sorted(candidates, key=lambda x: _filename_priority(x[0]), reverse=True)
            for c in candidates:
                path, offset, size = c
                return self.read_img_from_block(path, offset, size)
        except Exception:
            pass

    def get_avatar_from_avtdir(self, avtid) -> Image.Image | None:
        dir1, dir2 = avtid[:2], avtid[2:4]
        candidates = glob.glob(os.path.join(self.avt_dir, dir1, dir2, f"*{avtid}*"))
        candidates = sorted(set(candidates), key=_filename_priority, reverse=True)
        for cand in candidates:
            if os.path.isdir(cand):
                candidates.extend(os.path.join(cand, x) for x in os.listdir(cand))
        for cand in candidates:
            if os.path.isdir(cand):
                continue
            try:
                if cand.endswith(".bm"):
                    return self.read_bm_file(cand)
                else:
                    return Image.open(cand)
            except Exception:
                logger.exception("")
                pass

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        if not self._use_avt:
            return None
        avtid = md5(username.encode('utf-8'))

        if self.avt_db is not None:
            ret = self.get_avatar_from_avtdb(avtid)
            if ret is not None:
                return ret

        if self.avt_dir is not None:
            ret = self.get_avatar_from_avtdir(avtid)
            if ret is not None:
                return ret
        logger.warning("Avatar file for {} not found.".format(username))

    def save_avatar_to_avtdir(self, username: str, im: Image.Image):
        """Save a downloaded avatar to avtdir so it can be reused next time."""
        avtid = md5(username.encode('utf-8'))
        dir1, dir2 = avtid[:2], avtid[2:4]
        fname = os.path.join(self.avt_dir, dir1, dir2, f"user_{avtid}.png")
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        logger.info(f"Caching downloaded avatar for {username} to {fname}.")
        im.save(fname, 'PNG')

    def read_img_from_block(self, filename, pos, size):
        file_idx = pos >> 32
        fname = os.path.join(self.sfs_dir,
                'avatar.block.' + '{:05d}'.format(file_idx))
        # offset of each block file: 17 + len(path)
        start_pos = pos - file_idx * (2**32) + 16 + len(filename) + 1
        try:
            with open(fname, 'rb') as f:
                f.seek(start_pos)
                data = f.read(size)
                im = Image.open(io.BytesIO(data))
                return im
        except IOError as e:
            logger.warn("Cannot read avatar from {}: {}".format(fname, str(e)))
            return None

    def read_bm_file(self, fname):
        # history at https://github.com/ppwwyyxx/wechat-dump/pull/14
        with open(fname, 'rb') as f:
            # filesize is 36880=96x96x4+16
            size = (96, 96, 3)
            img = np.zeros(size, dtype='uint8')
            for i in range(96):
                for j in range(96):
                    r, g, b, a = f.read(4)
                    img[i,j] = (r, g, b)
            return Image.fromarray(img, mode="RGB")

    def _search_avt_db(self, avtid):
        conn = sqlite3.connect(self.avt_db)
        cursor = conn.execute("select FileName,Offset,Size from Index_avatar")
        candidates = []
        for path, offset, size in cursor:
            if avtid in path:
                candidates.append((path, offset, size))
        return candidates

if __name__ == '__main__':
    import sys
    r = AvatarReader(sys.argv[1], sys.argv[2])
    print(r.get_avatar(sys.argv[3]))
