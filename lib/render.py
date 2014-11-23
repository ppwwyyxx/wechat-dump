#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: render.py
# Date: Sun Nov 23 17:52:08 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import base64
LIB_PATH = os.path.dirname(os.path.abspath(__file__))
CSS_FILE = os.path.join(LIB_PATH, 'static/wx.css')
HTML_FILE = os.path.join(LIB_PATH, 'static/template.html')

try:
    from csscompressor import compress as css_compress
except:
    css_compress = lambda x: x

from .msg import *
from .utils import ensure_unicode

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG", TYPE_SPEAK: "TP_SPEAK"}
TEMPLATES = dict([(k, open(os.path.join(
    LIB_PATH, 'static/{}.html'.format(v))).read())
    for k, v in TEMPLATES_FILES.iteritems()])

class HTMLRender(object):
    def __init__(self, parser, res=None):
        self.css = ensure_unicode(css_compress(open(CSS_FILE).read()))
        self.html = ensure_unicode(open(HTML_FILE).read())
        self.parser = parser
        self.res = res

    def get_avatar_pair(self, username):
        """ return base64 string pair of two avatars"""
        if self.res is None:
            return ("", "")
        avt1 = self.res.get_avatar(self.parser.username)
        avt2 = self.res.get_avatar(username)
        return (avt1, avt2)

    def get_voice_mp3(self, imgpath):
        """ return base64 string"""
        if self.res is None:
            return ""
        amr_fpath = self.res.speak_data[imgpath]
        mp3_file = os.path.join('/tmp', os.path.basename(amr_fpath)[:-4] + '.mp3')
        os.system('sox {} {}'.format(amr_fpath, mp3_file))
        mp3_string = open(mp3_file, 'rb').read()
        os.unlink(mp3_file)
        return base64.b64encode(mp3_string)

    def render_msg(self, msg):
        """ render a message, return the block"""
        # TODO
        try:
            template = ensure_unicode(TEMPLATES[msg.type])
            if msg.type == TYPE_SPEAK:
                audio_str = self.get_voice_mp3(msg.imgPath)
                return template.format(sender_label='you' if not msg.isSend else 'me',
                                       voice_duration=10,
                                       voice_str=audio_str)
            else:
                raise
        except:
            template = ensure_unicode(TEMPLATES[1])
            return template.format(sender_label='you' if not msg.isSend else 'me',
                                   content=msg.msg_str())

    def render_msgs(self, msgs):
        talker_name = msgs[0].talker
        avatars = self.get_avatar_pair(talker_name)
        blocks = [self.render_msg(m) for m in msgs]
        return self.html.format(style=self.css, talker=msgs[0].talker_name,
                               messages=u''.join(blocks),
                               avatar_me=avatars[0],
                               avatar_you=avatars[1])

if __name__ == '__main__':
    r = HTMLRender()
    with open('/tmp/a.html', 'w') as f:
        print >> f, r.html.format(style=r.css, talker='talker',
                                     messages='haha')
