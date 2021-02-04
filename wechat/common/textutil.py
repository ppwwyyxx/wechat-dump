# -*- coding: utf-8 -*-

import hashlib
import base64

def ensure_unicode(s):
    if type(s) == str:
        return s
    elif type(s) == bytes:
        return s.decode('utf-8')
    raise TypeError(f"type of string is {type(s)}")


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
    filename = ensure_unicode(fname)
    import os
    if os.uname().sysname == 'Linux' :
        return "".join(
            [c for c in filename if (not ( c == '/' ) )]).rstrip()
    else :
        return "".join(
            [c for c in filename if c.isalpha() or c.isdigit() or c==' ']).rstrip()
