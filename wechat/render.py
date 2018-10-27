#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: render.py
# Date: Wed Nov 29 03:53:55 2017 -0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
import base64
import glob
from pyquery import PyQuery
import logging
logger = logging.getLogger(__name__)

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(LIB_PATH, 'static')
HTML_FILE = os.path.join(STATIC_PATH, 'TP_INDEX.html')
TIME_HTML_FILE = os.path.join(STATIC_PATH, 'TP_TIME.html')
FRIEND_AVATAR_CSS_FILE = os.path.join(STATIC_PATH, 'avatar.css.tpl')

try:
    from csscompressor import compress as css_compress
except ImportError:
    css_compress = lambda x: x

from .msg import *
from common.textutil import ensure_unicode
from common.progress import ProgressReporter
from common.timer import timing
from .smiley import SmileyProvider
from .msgslice import MessageSlicerByTime, MessageSlicerBySize

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG",
                   TYPE_IMG: "TP_IMG",
                   TYPE_SPEAK: "TP_SPEAK",
                   TYPE_EMOJI: "TP_EMOJI",
                   TYPE_CUSTOM_EMOJI: "TP_EMOJI",
                   TYPE_LINK: "TP_MSG",
                   TYPE_VIDEO_FILE: "TP_VIDEO"}
TEMPLATES = {k: ensure_unicode(open(os.path.join(STATIC_PATH, '{}.html'.format(v))).read())
    for k, v in TEMPLATES_FILES.iteritems()}

class HTMLRender(object):
    def __init__(self, parser, res=None):
        self.html = ensure_unicode(open(HTML_FILE).read())
        self.time_html = open(TIME_HTML_FILE).read()
        self.parser = parser
        self.res = res
        assert self.res is not None, \
            "Resource Directory not given. Cannot render HTML."
        self.smiley = SmileyProvider()

        css_files = glob.glob(os.path.join(LIB_PATH, 'static/*.css'))
        self.css_string = []    # css to add
        for css in css_files:
            logger.info("Loading {}".format(os.path.basename(css)))
            css = ensure_unicode((open(css).read()))
            self.css_string.append(css)

        js_files = glob.glob(os.path.join(LIB_PATH, 'static/*.js'))
        # to load jquery before other js
        js_files = sorted(js_files, key=lambda f: 'jquery-latest' in f, reverse=True)
        self.js_string = []
        for js in js_files:
            logger.info("Loading {}".format(os.path.basename(js)))
            js = ensure_unicode(open(js).read())
            self.js_string.append(js)

    @property
    def all_css(self):
        # call after processing all messages,
        # because smiley css need to be included only when necessary
        def process(css):
            css = css_compress(css)
            return u'<style type="text/css">{}</style>'.format(css)

        if hasattr(self, 'final_css'):
            return self.final_css + process(self.smiley.gen_used_smiley_css())

        self.final_css = u"\n".join(map(process, self.css_string))
        return self.final_css + process(self.smiley.gen_used_smiley_css())

    @property
    def all_js(self):
        if hasattr(self, 'final_js'):
            return self.final_js
        def process(js):
            # TODO: add js compress
            return u'<script type="text/javascript">{}</script>'.format(js)
        self.final_js = u"\n".join(map(process, self.js_string))
        return self.final_js

    #@timing(total=True)
    def render_msg(self, msg):
        """ render a message, return the html block"""
        # TODO for chatroom, add nickname on avatar
        sender = u'you ' + msg.talker if not msg.isSend else 'me'
        format_dict = {'sender_label': sender,
                       'time': msg.createTime }
        if(not msg.isSend and msg.is_chatroom()):
            format_dict['nickname'] = '>\n       <pre align=\'left\'>'+msg.talker_nickname+'</pre'
        else:
            format_dict['nickname'] = ' '
        def fallback():
            template = TEMPLATES[TYPE_MSG]
            content = msg.msg_str()
            format_dict['content'] = self.smiley.replace_smileycode(content)
            return template.format(**format_dict)

        template = TEMPLATES.get(msg.type)
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
            img = self.res.get_img(fnames)
            if not img:
                logger.warn("No image thumbnail found for {}".format(imgpath))
                return fallback()
            # TODO do not show fancybox when no bigimg found
            format_dict['img'] = (img, 'jpeg')
            return template.format(**format_dict)
        elif msg.type == TYPE_EMOJI or msg.type == TYPE_CUSTOM_EMOJI:
            if 'emoticonmd5' in msg.content:
                pq = PyQuery(msg.content)
                md5 = pq('emoticonmd5').text()
            else:
                md5 = msg.imgPath
                # TODO md5 could exist in both.
                # first is emoji md5, second is image2/ md5
                # can use fallback here.
            if md5:
                emoji_img, format = self.res.get_emoji_by_md5(md5)
                format_dict['emoji_format'] = format
                format_dict['emoji_img'] = emoji_img
            else:
                import IPython as IP; IP.embed()
            return template.format(**format_dict)
        elif msg.type == TYPE_LINK:
            content = msg.msg_str()
            # TODO show a short link with long href, if link too long
            if content.startswith(u'URL:'):
                url = content[4:]
                content = u'URL:<a target="_blank" href="{0}">{0}</a>'.format(url)
                format_dict['content'] = content
                return template.format(**format_dict)
        elif msg.type == TYPE_WX_VIDEO:
            # TODO: fetch video from resource
            return fallback()
        elif msg.type == TYPE_VIDEO_FILE:
            # TODO: fetch video from resource
            imgpath = msg.imgPath
            img = self.res.get_video(imgpath)
            format_dict['img'] = img
            return template.format(**format_dict)
        return fallback()

    def _render_partial_msgs(self, msgs):
        """ return single html"""
        self.smiley.used_smiley_id.clear()
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

        # string operation is extremely slow
        return self.html.format(extra_css=self.all_css,
                            extra_js=self.all_js,
                            chat=msgs[0].chat_nickname,
                            messages=u''.join(blocks)
                           )

    def prepare_avatar_css(self, talkers):
        avatar_tpl= ensure_unicode(open(FRIEND_AVATAR_CSS_FILE).read())
        my_avatar = self.res.get_avatar(self.parser.username)
        css = avatar_tpl.format(name='me', avatar=my_avatar)

        for talker in talkers:
            avatar = self.res.get_avatar(talker)
            css += avatar_tpl.format(name=talker, avatar=avatar)
        self.css_string.append(css)

    def render_msgs(self, msgs):
        """ render msgs of one chat, return a list of html"""
        if msgs[0].is_chatroom():
            talkers = set([m.talker for m in msgs])
        else:
            talkers = set([msgs[0].talker])
        self.prepare_avatar_css(talkers)

        self.res.cache_voice_mp3(msgs)

        chat = msgs[0].chat_nickname
        logger.info(u"Rendering {} messages of {}".format(
            len(msgs), chat))

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
