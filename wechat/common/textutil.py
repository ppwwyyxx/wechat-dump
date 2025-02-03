# -*- coding: UTF-8 -*-

import hashlib
import base64


def md5(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()

def get_file_b64(fname):
    with open(fname, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')

def get_file_md5(fname):
    with open(fname, 'rb') as f:
        return md5(f.read())

def safe_filename(fname):
    return "".join(
        [c for c in fname if c.isalpha() or c.isdigit() or c ==' ']).rstrip()
