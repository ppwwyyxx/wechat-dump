#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: smiley.py
# Date: Wed Dec 24 22:16:33 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import re
import json
LIB_PATH = os.path.dirname(os.path.abspath(__file__))

UNICODE_SMILEY_FILE = os.path.join(LIB_PATH, 'static', 'unicode-smiley.json')
TENCENT_SMILEY_FILE = os.path.join(LIB_PATH, 'static', 'tencent-smiley.json')
TENCENT_EXTRASMILEY_FILE = os.path.join(LIB_PATH,
                                       'static', 'tencent-smiley-extra.json')
UNICODE_SMILEY_RE = re.compile(
    u'[\U00010000-\U0010ffff]|[\u2600-\u2764]|\u2122|\u00a9|\u00ae|[\ue000-\ue5ff]')

class SmileyProvider(object):
    def __init__(self, html_replace=True):
        """ html_replace: replace smileycode by html.
            otherwise, replace by plain text
        """
        self.html_replace = html_replace
        if not html_replace:
            raise NotImplementedError()

        # [微笑] -> 0
        self.tencent_smiley = json.load(open(TENCENT_SMILEY_FILE))

        # some extra smiley from javascript on wx.qq.com
        extra_smiley = json.load(open(TENCENT_EXTRASMILEY_FILE))
        extra_smiley = {u'[' + k + u']': v for k, v in
                            extra_smiley.iteritems()}
        self.tencent_smiley.update(extra_smiley)

        # 1f35c -> "\ue340"
        #self.unicode_smiley_code = gUnicodeCodeMap

        # u'\U0001f35c' -> "e340"   # for iphone
        # u'\ue415' -> 'e415'       # for android
        unicode_smiley_dict = json.load(open(UNICODE_SMILEY_FILE))
        self.unicode_smiley = {unichr(int(k, 16)): hex(ord(v))[2:] for k, v in
                                unicode_smiley_dict.iteritems()}
        self.unicode_smiley.update({v: hex(ord(v))[2:] for _, v in
                                unicode_smiley_dict.iteritems()})
        self.used_smiley_id = set()


    def gen_replace_elem(self, smiley_id):
        return '<span class="smiley smiley{}"></span>'.format(smiley_id)

    def _replace_unicode(self, msg):
        if not UNICODE_SMILEY_RE.findall(msg):
        # didn't find the code
            return msg
        for k, v in self.unicode_smiley.iteritems():
            if k in msg:
                self.used_smiley_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def _replace_tencent(self, msg):
        if (not '[' in msg or not ']' in msg) \
           and (not '/:' in msg) and (not '/' in msg):
            return msg
        for k, v in self.tencent_smiley.iteritems():
            if k in msg:
                self.used_smiley_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def replace_smileycode(self, msg):
        """ replace the smiley code in msg
            return a html
        """
        msg = self._replace_unicode(msg)
        msg = self._replace_tencent(msg)
        return msg

if __name__ == '__main__':
    smiley = SmileyProvider()
    msg = u"[挥手]哈哈呵呵ｈｉｈｉ\U0001f684\u2728\u0001 /::<\ue415"
    msg = smiley.replace_smileycode(msg)
    print msg
