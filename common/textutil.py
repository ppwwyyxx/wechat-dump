#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: utils.py
# Date: Wed Jun 17 23:59:25 2015 +0800
# Author: Yuxin Wu

import hashlib
import base64

def ensure_bin_str(s):
    if type(s) == str:
        return s
    if type(s) == unicode:
        return s.encode('utf-8')

def ensure_unicode(s):
    if type(s) == str:
        return s.decode('utf-8')
    if type(s) == unicode:
        return s


def md5(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()

def get_file_b64(fname):
    data = open(fname, 'rb').read()
    return base64.b64encode(data)

def safe_filename(fname):
    filename = ensure_unicode(fname)
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c==' ']).rstrip()
