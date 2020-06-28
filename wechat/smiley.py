#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import functools
import re
import json
import struct

from common.textutil import get_file_b64

STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TENCENT_SMILEY_FILE = os.path.join(STATIC_PATH, 'tencent-smiley.json')

try:
    UNICODE_SMILEY_RE = re.compile(
        u'[\U00010000-\U0010ffff]|[\u2600-\u2764]|\u2122|\u00a9|\u00ae|[\ue000-\ue5ff]'
    )
except re.error:
    # UCS-2 build
    UNICODE_SMILEY_RE = re.compile(
        u'[\uD800-\uDBFF][\uDC00-\uDFFF]|[\u2600-\u2764]|\u2122|\u00a9|\u00ae|[\ue000-\ue5ff]'
    )


HEAD = """.smiley {
    padding: 1px;
    background-position: -1px -1px;
    background-repeat: no-repeat;
    width: 20px;
    height: 20px;
    display: inline-block;
    vertical-align: top;
    zoom: 1;
}
"""

TEMPLATE = """.{name} {{
    background-image: url("data:image/png;base64,{b64}");
    background-size: 24px 24px;
}}"""

def _css_class_name(s):
    s = s.replace("/", "_")
    s = s.replace(".", "_")
    return "smiley_" + s

class SmileyProvider(object):
    def __init__(self, html_replace=True):
        """ html_replace: replace smileycode by html.
            otherwise, replace by plain text
        """
        self.html_replace = html_replace
        if not html_replace:
            raise NotImplementedError()

        # [微笑] -> smiley/0.png
        self.tencent_smiley = json.load(open(TENCENT_SMILEY_FILE))
        self.used_smileys = set()

    def reset(self):
        self.used_smileys.clear()

    def gen_replace_elem(self, smiley_path):
        self.used_smileys.add(str(smiley_path))
        return '<span class="smiley {}"></span>'.format(_css_class_name(smiley_path))

    def replace_smileycode(self, msg):
        """ replace the smiley code in msg
            return a html
        """
        # pre-filter:
        if ('[' not in msg) and ('/' not in msg) and not UNICODE_SMILEY_RE.findall(msg):
            return msg
        for k, v in self.tencent_smiley.items():
            if k in msg:
                msg = msg.replace(k, self.gen_replace_elem(v))
        return msg
        return msg

    def gen_used_smiley_css(self):
        ret = HEAD
        for path in self.used_smileys:
            fname = os.path.join(STATIC_PATH, path)
            b64 = get_file_b64(fname)
            ret = ret + TEMPLATE.format(name=_css_class_name(path), b64=b64)
        return ret

if __name__ == '__main__':
    smiley = SmileyProvider()
    msg = u"[挥手]哈哈呵呵ｈｉｈｉ\U0001f684\u2728\u0001 /::<\ue415"
    msg = smiley.replace_smileycode(msg)
    smiley.gen_used_smiley_css()
