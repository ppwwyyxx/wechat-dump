#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: create_table.py
# Date: Wed Mar 25 16:43:22 2015 +0800
# Author: Yuxin Wu

import sys
import os

from libchat import SqliteLibChat

if len(sys.argv) != 2:
    print "Usage: {} <DB file name>"
    sys.exit()

db_name = sys.argv[1]

if os.path.exists(db_name):
    delete = raw_input("DB exists. Delete ? (y/n)")
    if delete == 'y':
        os.unlink(db_name)
    else:
        sys.exit()

db = SqliteLibChat(db_name)
db.create()
