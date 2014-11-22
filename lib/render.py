#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: Render.py
# Date: Sat Nov 22 22:29:56 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
LIB_PATH = os.path.dirname(os.path.abspath(__file__))
CSS_FILE = os.path.join(LIB_PATH, 'static/wx.css')
HTML_FILE = os.path.join(LIB_PATH, 'static/template.html')

class HTMLRender(object):
    def __init__(self, res=None):
        self.css = open(CSS_FILE).read().replace('\n', '')
        self.html = open(HTML_FILE).read()
        self.res = res

    def render_msg(self, msg):
        """ render a message"""
        # TODO
        pass

if __name__ == '__main__':
    r = HTMLRender()
    with open('/tmp/a.html', 'w') as f:
        print >> f, r.html.format(style=r.css, talker='talker',
                                     messages='haha')
