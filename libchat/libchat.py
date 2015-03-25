#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: libchat.py
# Date: Wed Mar 25 16:43:40 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>
import sqlite3
import os

class SqliteLibChat(object):

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)

    def create(self):
        c = self.conn.cursor()
        c.execute("""
          CREATE TABLE message (
          source SMALLINT,
          time INTEGER,
          sender TEXT,
          chatroom TEXT,
          image COLLATE BINARY,
          sound COLLATE BINARY,
          extra_data COLLATE BINARY
         )
          """)
        self.conn.commit()
