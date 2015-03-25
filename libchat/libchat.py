#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: libchat.py
# Date: Wed Mar 25 22:46:51 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>
import sqlite3
import os
from collections import namedtuple

SOURCE_ID = {'wechat': 0}
NUM_FIELDS = 8
ChatMsgBase = namedtuple('ChatMsgBase',
          ['source', 'time', 'sender', 'chatroom',
           'text', 'image', 'sound', 'extra_data'])
class ChatMsg(ChatMsgBase):
    def __repr__(self):
        return "Msg@{}/{}-{}/{}/{}/{}/{}".format(
            self.time, self.sender, self.chatroom,
            self.text.encode('utf-8'), 'IMG' if self.image else '',
            'AUD' if self.sound else '', self.extra_data)

class SqliteLibChat(object):
    """ Interface for interacting with LibChat database"""

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()

    def create(self):
        self.c.execute("""
          CREATE TABLE message (
          source SMALLINT,
          time INTEGER,
          sender TEXT,
          chatroom TEXT,
          text TEXT,
          image COLLATE BINARY,
          sound COLLATE BINARY,
          extra_data COLLATE BINARY
         )
          """)
        self.conn.commit()

    def _add_msg(self, tp):
        assert isinstance(tp, ChatMsg)
        self.c.execute(
          """INSERT INTO message VALUES ({0})""".format(
              ','.join(['?']*NUM_FIELDS)), tp)

    def add_msgs(self, msgs):
        self.c = self.conn.cursor()
        for m in msgs:
            self._add_msg(SqliteLibChat.prefilter(m))
            self.conn.commit()

    @staticmethod
    def prefilter(msg):
        source = msg.source
        if isinstance(source, basestring):
            source = SOURCE_ID[source]
        return ChatMsg(source, *msg[1:])


    def iterate_all_msg(self, predicate=None):
        """ predicate: a dict used as SELECT filter
            return a generator for all messages
        """
        if predicate is None:
            self.c.execute("SELECT * FROM message")
        else:
            self.c.execute("SELECT * FROM message WHERE {}".format(
                ' AND '.join(["{} = {}".format(k, v)
                              for k, v in predicate.iteritems()])))
        for row in self.c.fetchall():
            yield ChatMsg(
                *row[:5],
                image=str(row[5]),
                sound=str(row[6]),
                extra_data=str(row[7])
            )   # use str to get raw bytes


if __name__ == '__main__':
    msg = ChatMsg(-1, 1000, 'me', 'room', 'hello', '\x01\x02\x03', '', '')
    db = SqliteLibChat('./message.db')
    #db.add_msgs([msg])
    for k in db.get_all_msg():
        print k

