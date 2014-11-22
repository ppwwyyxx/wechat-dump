#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: Res.py
# Date: Sat Nov 22 20:54:25 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import glob
import os

VOICE_DIRNAME = 'voice2'

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, res_dir):
        assert os.path.isdir(res_dir), "No such directory: {}".format(res_dir)
        self.res_dir = res_dir
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




