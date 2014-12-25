#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: render.py
# Date: Thu Dec 25 22:05:41 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import base64
import glob
import logging
logger = logging.getLogger(__name__)

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(LIB_PATH, 'static', 'template.html')
TIME_HTML_FILE = os.path.join(LIB_PATH, 'static', 'TP_TIME.html')

try:
    from csscompressor import compress as css_compress
except:
    css_compress = lambda x: x

from .msg import *
from .utils import ensure_unicode, ProgressReporter, pmap, timing
from .smiley import SmileyProvider
from .msgslice import MessageSlicerByTime, MessageSlicerBySize

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG",
                   TYPE_IMG: "TP_IMG",
                   TYPE_SPEAK: "TP_SPEAK",
                   TYPE_EMOJI: "TP_EMOJI",
                   TYPE_LINK: "TP_MSG"}
TEMPLATES = {k: ensure_unicode(open(os.path.join(LIB_PATH, 'static/{}.html'.format(v))).read())
    for k, v in TEMPLATES_FILES.iteritems()}

class HTMLRender(object):
    def __init__(self, parser, res=None):
        self.html = ensure_unicode(open(HTML_FILE).read())
        self.time_html = open(TIME_HTML_FILE).read()
        self.parser = parser
        self.res = res
        if self.res is None:
            logger.warn("Resource Directory not given. Images / Voice Message won't be displayed.")
        self.smiley = SmileyProvider()

        csss = glob.glob(os.path.join(LIB_PATH, 'static/*.css'))
        css_string = []
        for css in csss:
            logger.info("Loading {}".format(os.path.basename(css)))
            css = ensure_unicode(css_compress(open(css).read()))
            css = u'<style type="text/css">{}</style>'.format(css)
            css_string.append(css)
        self.css_string = u"\n".join(css_string)

        jss = glob.glob(os.path.join(LIB_PATH, 'static/*.js'))
        js_string = []
        for js in jss:
            logger.info("Loading {}".format(os.path.basename(js)))
            js = ensure_unicode(open(js).read())
            # TODO: add js compress
            js = u'<script type="text/javascript">{}</script>'.format(js)
            js_string.append(js)
        self.js_string = u"\n".join(js_string)

    def get_avatar_pair(self, username):
        """ return base64 string pair of two avatars"""
        if self.res is None:
            return ("", "")
        avt1 = self.res.get_avatar(self.parser.username)
        avt2 = self.res.get_avatar(username)
        return (avt1, avt2)

    def render_msg(self, msg):
        """ render a message, return the html block"""
        sender = 'you' if not msg.isSend else 'me'
        format_dict = {'sender_label': sender,
                       'time': msg.createTime }
        def fallback():
            template = TEMPLATES[TYPE_MSG]
            content = msg.msg_str()
            format_dict['content'] = self.smiley.replace_smileycode(content)
            return template.format(**format_dict)

        if msg.type not in TEMPLATES:
            return fallback()

        template = TEMPLATES[msg.type]
        if msg.type == TYPE_SPEAK:
            audio_str, duration = self.res.get_voice_mp3(msg.imgPath)
            format_dict['voice_duration'] = duration
            format_dict['voice_str'] = audio_str
            return template.format(**format_dict)
        elif msg.type == TYPE_IMG:
            # imgPath was original THUMBNAIL_DIRPATH://th_xxxxxxxxx
            imgpath = msg.imgPath.split('_')[-1]
            if not imgpath:
                logger.warn('No imgpath in an image message. Perhaps a bug in wechat.')
                return fallback()
            bigimgpath = self.parser.imginfo.get(msg.msgSvrId)
            fnames = [k for k in [imgpath, bigimgpath] if k]
            bigimg, smallimg = self.res.get_img(fnames)
            if not smallimg:
                logger.warn("No image thumbnail found for {}".format(imgpath))
                return fallback()
            # TODO do not show fancybox when no bigimg found
            format_dict['small_img'] = smallimg
            format_dict['big_img'] = bigimg
            return template.format(**format_dict)
        elif msg.type == TYPE_EMOJI:
            imgpath = msg.imgPath
            if imgpath in self.parser.internal_emojis:
                emoji_img, format = self.res.get_internal_emoji(self.parser.internal_emojis[imgpath])
            else:
                if imgpath in self.parser.emojis:
                    group, _ = self.parser.emojis[imgpath]
                else:
                    group = None
                emoji_img, format = self.res.get_emoji(imgpath, group)
            format_dict['emoji_format'] = format
            format_dict['emoji_img'] = emoji_img
            return template.format(**format_dict)
        elif msg.type == TYPE_LINK:
            content = msg.msg_str()
            if content.startswith(u'URL:'):
                url = content[4:]
                content = u'URL:<a target="_blank" href="{0}">{0}</a>'.format(url)
                format_dict['content'] = content
                return template.format(**format_dict)
        return fallback()

    def _render_partial_msgs(self, msgs):
        """ return single html"""
        slicer = MessageSlicerByTime()
        slices = slicer.slice(msgs)

        blocks = []
        for idx, slice in enumerate(slices):
            nowtime = slice[0].createTime
            if idx == 0 or \
               slices[idx - 1][0].createTime.date() != nowtime.date():
                timestr = nowtime.strftime("%m/%d %H:%M:%S")
            else:
                timestr = nowtime.strftime("%H:%M:%S")
            blocks.append(self.time_html.format(time=timestr))
            blocks.extend([self.render_msg(m) for m in slice])
            self.prgs.trigger(len(slice))

        return self.html.format(extra_css=self.css_string,
                                extra_js=self.js_string,
                                talker=msgs[0].talker_name,
                                messages=u''.join(blocks),
                                avatars=self.avatars)

    def render_msgs(self, msgs):
        """ render msgs of one friend, return a list of html"""
        talker_name = msgs[0].talker
        self.avatars = self.get_avatar_pair(talker_name)
        logger.info(u"Rendering {} messages of {}({})".format(
            len(msgs), self.parser.contacts[talker_name], talker_name))

        self.prgs = ProgressReporter("Render", total=len(msgs))
        slice_by_size = MessageSlicerBySize().slice(msgs)
        ret = [self._render_partial_msgs(s) for s in slice_by_size]
        self.prgs.finish()
        return ret

if __name__ == '__main__':
    r = HTMLRender()
    with open('/tmp/a.html', 'w') as f:
        print >> f, r.html.format(style=r.css, talker='talker',
                                     messages='haha')
