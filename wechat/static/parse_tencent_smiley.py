#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: parse_tencent_smiley.py
# Date: Sat Dec 27 00:15:14 2014 +0800
# Author: Yuxin Wu

import xml.etree.ElementTree as ET
import os
import json

tree = ET.parse(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'smiley.xml'))
root = tree.getroot()

smileys = {}
for child in root:
    name = child.attrib['name']
    if 'smiley_values' in name:
        if '_th' in name:
            continue        # ignore thailand language
        lst = [c.text for c in child]
        assert len(lst) == 105
        for idx, v in enumerate(lst):
            if type(v) == str:
                # two code appears in the xml.. don't know why
                v = v.strip('"')
                v = v.replace('&lt;', '<')
                v = v.replace('&amp;', '&')
                v = v.decode('utf-8')
            smileys[v] = idx

with open('tencent-smiley.json', 'w') as f:
    json.dump(smileys, f)

