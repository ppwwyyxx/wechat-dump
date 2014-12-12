#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: render.py
# Date: Fri Dec 12 23:15:31 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import base64
import eyed3
import logging
logger = logging.getLogger(__name__)
LIB_PATH = os.path.dirname(os.path.abspath(__file__))
CSS_FILE = os.path.join(LIB_PATH, 'static/wx.css')
HTML_FILE = os.path.join(LIB_PATH, 'static/template.html')

try:
    from csscompressor import compress as css_compress
except:
    css_compress = lambda x: x

from .msg import *
from .utils import ensure_unicode

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG",
                   TYPE_SPEAK: "TP_SPEAK",
                   TYPE_IMG: "TP_IMG"}
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
        """ return base64 string, and voice duration"""
        if self.res is None:
            return ""
        amr_fpath = self.res.speak_data[imgpath]
        mp3_file = os.path.join('/tmp', os.path.basename(amr_fpath)[:-4] + '.mp3')
        # TODO is there a library to use?
        ret = os.system('sox {} {}'.format(amr_fpath, mp3_file))
        if ret != 0:
            logger.warn("Sox Failed!")
            return ""
        mp3_string = open(mp3_file, 'rb').read()
        duration = eyed3.load(mp3_file).info.time_secs
        os.unlink(mp3_file)
        return base64.b64encode(mp3_string), duration

    def render_msg(self, msg):
        """ render a message, return the html block"""
        # TODO
        try:
            template = ensure_unicode(TEMPLATES[msg.type])
            if msg.type == TYPE_SPEAK:
                audio_str, duration = self.get_voice_mp3(msg.imgPath)
                return template.format(sender_label='you' if not msg.isSend else 'me',
                                       voice_duration=duration,
                                       voice_str=audio_str)
            elif msg.type == TYPE_IMG:
                # imgPath was original THUMBNAIL_DIRPATH://th_xxxxxxxxx
                imgpath = msg.imgPath.split('_')[-1]
                bigimgpath = self.parser.imginfo.get(msg.msgSvrId)

                bigimg, smallimg = self.res.get_img([imgpath, bigimgpath])
                return template.format(sender_label='you' if not msg.isSend else 'me',
                                       img_data=smallimg)
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
