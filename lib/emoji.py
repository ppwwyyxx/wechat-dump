#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: emoji.py
# Date: Mon Dec 15 22:30:24 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import re
LIB_PATH = os.path.dirname(os.path.abspath(__file__))

from emojiname import gQQFaceMap as gBracketFace
from emojiname import gUnicodeFaceMap as gUnicodeFace
from emojiname import gEmojiCodeMap as gUnicodeCodeMap
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
        self.bracket_face = dict([(('[' + k + ']').decode('utf-8'), v)
                                 for k, v in gBracketFace.iteritems()])

        # 1f35c -> "\ue340"
        #self.unicode_face_code = gUnicodeCodeMap

        # u'\U0001f35c' -> "e340"
        self.unicode_face = dict([(unichr(int(k, 16)), v[2:])
                                for k, v in gUnicodeCodeMap.iteritems()])
        self.used_emoji_id = set()


    def gen_replace_elem(self, emoji_id):
        return '<span class="emoji emoji{}"></span>'.format(emoji_id)

    def _replace_unicode(self, msg):
        if not UNICODE_EMOJI_RE.findall(msg):
        # didn't find the code
            return msg
        for k, v in self.unicode_face.iteritems():
            if k in msg:
                self.used_emoji_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def _replace_bracket(self, msg):
        if not '[' in msg or not ']' in msg:
            return msg
        for k, v in self.bracket_face.iteritems():
            if k in msg:
                self.used_emoji_id.add(v)
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg

    def replace_emojicode(self, msg):
        """ replace the emoji code in msg
            return a html
        """
        msg = self._replace_unicode(msg)
        msg = self._replace_bracket(msg)
        return msg

if __name__ == '__main__':
    emoji = EmojiProvider()
    msg = u"[挥手]哈哈呵呵ｈｉｈｉ\U0001f684\u2728\u0001"
    msg = emoji.replace_emojicode(msg)
    print msg
