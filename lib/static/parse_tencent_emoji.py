#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: parse_tencent_emoji.py
# Date: Tue Dec 16 23:22:50 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import xml.etree.ElementTree as ET
import os
import json

NUM_EMOJI = 105

tree = ET.parse(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'emoji.xml'))
root = tree.getroot()

emojis = {}
for child in root:
    name = child.attrib['name']
    if 'smiley_values' in name:
        if '_th' in name:
            continue        # ignore thailand language
        lst = [c.text for c in child]
        assert len(lst) == 105
        for idx, v in enumerate(lst):
            if type(v) == str:
                v = v.decode('utf-8')
            emojis[v] = idx

with open('tencent-emoji.json', 'w') as f:
    json.dump(emojis, f)

