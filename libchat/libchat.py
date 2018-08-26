#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: libchat.py
# Date: Sun Apr 12 21:08:51 2015 +0900
# Author: Yuxin Wu
import sqlite3
import os
from datetime import datetime
import time
from collections import namedtuple

SOURCE_ID = {'wechat': 0}
NUM_FIELDS = 8
ChatMsgBase = namedtuple('ChatMsgBase',
          ['source', 'time', 'sender', 'chatroom',
           'text', 'image', 'sound', 'extra_data'])
""" source: unicode,
    time: datetime,
    sender: unicode,
    chatroom: unicode,
    text: unicode,
    image: string,
    sound: string,
    extra_data: string
"""

class ChatMsg(ChatMsgBase):
    def __repr__(self): # repr must return str?
        return "Msg@{}/{}-{}/{}/{}/{}/{}".format(
            self.time, self.sender.encode('utf-8'),
            self.chatroom.encode('utf-8'),
            self.text.encode('utf-8'), 'IMG' if self.image else '',
            'AUD' if self.sound else '', self.extra_data)

class SqliteLibChat(object):
    """ Interface for interacting with LibChat database"""

    def __init__(self, db_file):
        self.db_file = db_file
        exist = os.path.isfile(db_file)
        self.conn = sqlite3.connect(db_file)
        self.conn.text_factory = str    # to allow use of raw-byte string
        self.c = self.conn.cursor()

        if not exist:
            self.create()

    def create(self):
        self.c.execute("""
          CREATE TABLE message (
          source SMALLINT,
          time TEXT,
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
        """ each message is a ChatMsg instance"""
        self.c = self.conn.cursor()
        for m in msgs:
            self._add_msg(SqliteLibChat.prefilter(m))
        self.conn.commit()

    @staticmethod
    def prefilter(msg):
        source = msg.source
        if isinstance(source, basestring):
            source = SOURCE_ID[source]
        tm = int(time.mktime(msg[1].timetuple()))
        return ChatMsg(source, tm, *msg[2:])

    @staticmethod
    def postfilter(msg):
        # source
        text = msg[4].decode('utf-8')
        time = datetime.fromtimestamp(int(msg[1]))
        return ChatMsg(msg[0], time, msg[2], msg[3],
                       text=text, image=msg[5],
                       sound=msg[6], extra_data=msg[7])

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
            yield ChatMsg(*SqliteLibChat.postfilter(row))


if __name__ == '__main__':
    db = SqliteLibChat(os.path.join(
        os.path.dirname(__file__), './message.db'))

    #msg = ChatMsg(-1, 1000, 'me', 'room', 'hello', '\x01\x02\x03', '', '')
    #db.add_msgs([msg])

    for k in db.iterate_all_msg():
        from IPython import embed; embed()
        print k

