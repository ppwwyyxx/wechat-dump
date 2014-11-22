#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: render.py
# Date: Sat Nov 22 23:24:10 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
LIB_PATH = os.path.dirname(os.path.abspath(__file__))
CSS_FILE = os.path.join(LIB_PATH, 'static/wx.css')
HTML_FILE = os.path.join(LIB_PATH, 'static/template.html')

try:
    from csscompressor import compress as css_compress
except:
    css_compress = lambda x: x

from .msg import *
from .utils import ensure_unicode

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG"}
TEMPLATES = dict([(k, open(os.path.join(
    LIB_PATH, 'static/{}.html'.format(v))).read())
    for k, v in TEMPLATES_FILES.iteritems()])



class HTMLRender(object):
    def __init__(self, res=None):
        self.css = ensure_unicode(css_compress(open(CSS_FILE).read()))
        self.html = ensure_unicode(open(HTML_FILE).read())
        self.res = res

    def render_msg(self, msg):
        """ render a message, return the block"""
        # TODO
        #template = ensure_unicode(TEMPLATES[msg.type])
        template = ensure_unicode(TEMPLATES[1])
        if False:
            return ""
        else:
            return template.format(sender_label='you' if not msg.isSend else 'me',
                                   content=msg.msg_str())

    def render_msgs(self, msgs):
        blocks = [self.render_msg(m) for m in msgs]
        return self.html.format(style=self.css, talker=msgs[0].talker_name,
                               messages=u''.join(blocks))

if __name__ == '__main__':
    r = HTMLRender()
    with open('/tmp/a.html', 'w') as f:
        print >> f, r.html.format(style=r.css, talker='talker',
                                     messages='haha')
