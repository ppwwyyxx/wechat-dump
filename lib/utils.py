#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: utils.py
# Date: Fri Nov 21 13:42:56 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

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
