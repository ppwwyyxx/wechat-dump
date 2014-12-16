#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: emoji.py
# Date: Tue Dec 16 23:49:40 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import re
import json
LIB_PATH = os.path.dirname(os.path.abspath(__file__))

UNICODE_EMOJI_FILE = os.path.join(LIB_PATH, 'static', 'unicode-emoji.json')
TENCENT_EMOJI_FILE = os.path.join(LIB_PATH, 'static', 'tencent-emoji.json')
TENCENT_EXTRAEMOJI_FILE = os.path.join(LIB_PATH,
                                       'static', 'tencent-emoji-extra.json')
UNICODE_EMOJI_RE = re.compile(u'[\U00010000-\U0010ffff]|[\u2600-\u2764]|\u2122|\u00a9|\u00ae')

class EmojiProvider(object):
    def __init__(self, html_replace=True):
        """ html_replace: replace emojicode by html.
            otherwise, replace by plain text
        """
        self.html_replace = html_replace
        if not html_replace:
            raise NotImplementedError()

        # [微笑] -> 0
        self.tencent_emoji = json.load(open(TENCENT_EMOJI_FILE))

        # some extra emoji from javascript on wx.qq.com
        extra_emoji = json.load(open(TENCENT_EXTRAEMOJI_FILE))
        extra_emoji = dict([(u'[' + k + u']', v) for k, v in
                            extra_emoji.iteritems()])
        self.tencent_emoji.update(extra_emoji)

        # 1f35c -> "\ue340"
        #self.unicode_emoji_code = gUnicodeCodeMap

        # u'\U0001f35c' -> "e340"
        self.unicode_emoji = dict([(unichr(int(k, 16)), hex(ord(v))[2:])
                                for k, v in
                                  json.load(open(UNICODE_EMOJI_FILE)).iteritems()])
        print self.unicode_emoji.items()[0]
        self.used_emoji_id = set()


    def gen_replace_elem(self, emoji_id):
        return '<span class="emoji emoji{}"></span>'.format(emoji_id)

    def _replace_unicode(self, msg):
        if not UNICODE_EMOJI_RE.findall(msg):
        # didn't find the code
            return msg
        for k, v in self.unicode_emoji.iteritems():
            if k in msg:
                self.used_emoji_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def _replace_tencent(self, msg):
        if (not '[' in msg or not ']' in msg) \
           and (not '\:' in msg) and (not '/' in msg):
            return msg
        for k, v in self.tencent_emoji.iteritems():
            if k == u'[挥手]':
                print k
                print type(k)
            if k in msg:
                self.used_emoji_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def replace_emojicode(self, msg):
        """ replace the emoji code in msg
            return a html
        """
        msg = self._replace_unicode(msg)
        msg = self._replace_tencent(msg)
        return msg

if __name__ == '__main__':
    emoji = EmojiProvider()
    msg = u"[挥手]哈哈呵呵ｈｉｈｉ\U0001f684\u2728\u0001"
    msg = emoji.replace_emojicode(msg)
    print msg
