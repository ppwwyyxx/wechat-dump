#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import xml.etree.ElementTree as ET
import struct
import os
import json


def parse_smiley_xml():
    ret = {}
    tree = ET.parse('smiley.xml')
    root = tree.getroot()

    for child in root:
        name = child.attrib['name']
        if 'smiley_values' not in name:
            continue
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
            ret[v] = os.path.join("smileys", f"{idx}.png")
    return ret


def parse_extra_smiley():
    # some extra smiley from javascript on wx.qq.com
    with open("tencent-smiley-extra.json") as f:
        obj = json.load(f)
    extra = {'[' + k + ']': os.path.join("smileys", f"{v}.png") for k, v in obj.items()}
    return extra

def parse_new_emoji():
    ret = {}
    xmlfile = "newemoji/newemoji-config.xml"
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    for child in root:
        assert child.tag == "emoji"
        vals = {k.tag: k.text for k in child}
        filename = os.path.join("newemoji", vals["fileName"])
        for k, v in vals.items():
            if "-value" in k:
                ret[v] = filename
    return ret

def parse_unicode_smiley():
    # 1f35c -> "\ue340"
    #self.unicode_smiley_code = gUnicodeCodeMap

    # u'\U0001f35c' -> "e340"   # for iphone
    # u'\ue415' -> 'e415'       # for android
    def unichar(i):
        try:
            return chr(i)
        except ValueError:
            return struct.pack('i', i).decode('utf-32')

    ret = {}
    with open("unicode-smiley.json") as f:
        d = json.load(f)
    for k, v in d.items():
        fname = os.path.join("smileys", hex(ord(v))[2:] + ".png")
        ret[unichar(int(k, 16))] = fname
        ret[v] = fname
    return ret

if __name__ == "__main__":
    # parse old smileys
    smileys = {}
    def add(dic, name):
        smileys.update(dic)
        print(f"Found {len(dic)} smileys from {name}. Total is {len(smileys)}")

    add(parse_smiley_xml(), "smiley.xml")
    add(parse_extra_smiley(), "tencent-smiley-extra.json")
    add(parse_new_emoji(), "newemoji")
    add(parse_unicode_smiley(), "unicode-smiley.json")

    with open('tencent-smiley.json', 'w') as f:
        json.dump(smileys, f, indent=2)
