#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: Msg.py
# Date: Fri Nov 21 12:15:27 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

from datetime import datetime

class WeChatMsg(object):
    """ fields in concern"""
    FIELDS = ["msgSvrId","type","isSend","createTime","talker","content","imgPath"]

    def __init__(self, row):
        """ row: a tuple corresponding to FIELDS"""
        assert len(row) == len(WeChatMsg.FIELDS)
        for f, v in zip(WeChatMsg.FIELDS, row):
            setattr(self, f, v)
        self.createTime = datetime.fromtimestamp(self.createTime / 1000)
        if self.content:
            self.content = self.content.encode('utf-8')

    def __repr__(self):
        return "{}:{}:{}".format(self.talker.encode('utf-8') if not self.isSend else 'me', self.createTime, self.content)
