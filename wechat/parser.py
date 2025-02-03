# -*- coding: UTF-8 -*-

import sqlite3
from collections import defaultdict, Counter
import itertools
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from .msg import WeChatMsg, TYPE_SYSTEM

""" tables in concern:
emojiinfo
imginfo2
addr_upload2
chatroom
message
rcontact
img_flag
"""

class WeChatDBParser(object):
    FIELDS = ["msgSvrId","type","isSend","createTime","talker","content","imgPath"]

    def __init__(self, db_fname):
        """ db_fname: a decrypted EnMicroMsg.db"""
        self.db_fname = db_fname
        self.db_conn = sqlite3.connect(self.db_fname)
        self.db_conn_bytes = sqlite3.connect(self.db_fname)
        # https://stackoverflow.com/questions/22751363/sqlite3-operationalerror-could-not-decode-to-utf-8-column
        self.db_conn_bytes.text_factory = lambda b: b
        self.cc = self.db_conn.cursor()

        self.contacts = {}      # username -> nickname
        self.contacts_rev = defaultdict(list)
        self.msgs_by_chat = defaultdict(list)
        self.emoji_groups = {}
        self.emoji_info = {}
        self.emoji_encryption_key = None
        self.avatar_urls = {}
        self._parse()

    def _parse_contact(self):
        contacts = self.cc.execute(
"""
SELECT username,conRemark,nickname FROM rcontact
""")
        for row in contacts:
            username, remark, nickname = row
            if remark:
                self.contacts[username] = remark
            else:
                self.contacts[username] = nickname

        for k, v in self.contacts.items():
            self.contacts_rev[v].append(k)
        logger.info("Found {} names in `contact` table.".format(len(self.contacts)))

    def _parse_msg(self):
        msgs_tot_cnt = 0
        db_msgs = self.db_conn_bytes.cursor().execute(
"""
SELECT {} FROM message
""".format(','.join(WeChatDBParser.FIELDS)))
        unknown_type_cnt = Counter()
        for row in db_msgs:
            values = self._parse_msg_row(row)
            if not values:
                continue
            msg = WeChatMsg(values)
            # TODO keep system message?
            if not WeChatMsg.filter_type(msg.type):
                self.msgs_by_chat[msg.chat].append(msg)
            if not msg.known_type:
                unknown_type_cnt[msg.type] += 1
        logger.warning("[Parser] Unhandled messages (type->cnt): {}".format(unknown_type_cnt))

        for k, v in self.msgs_by_chat.items():
            self.msgs_by_chat[k] = sorted(v, key=lambda x: x.createTime)
            msgs_tot_cnt += len(v)
        logger.info("Found {} message records.".format(msgs_tot_cnt))

    def _parse_userinfo(self):
        userinfo_q = self.cc.execute(""" SELECT id, value FROM userinfo """)
        userinfo = dict(userinfo_q)
        self.username = userinfo.get(2, None)
        if self.username is None:
            nickname = userinfo.get(4, None)
            if nickname is not None:
                self.username = self.contacts_rev.get(nickname, [None])[0]
        if self.username is None:
            logger.error("Cannot find username in userinfo table!")
            self.username = input("Please enter your username:")
        assert isinstance(self.username, str), self.username
        logger.info("Your username is: {}".format(self.username))

    def _parse_imginfo(self):
        imginfo_q = self.cc.execute("""SELECT msgSvrId, bigImgPath FROM ImgInfo2""")
        self.imginfo = {k: v for (k, v) in imginfo_q
                             if not v.startswith('SERVERID://')}
        logger.info("Found {} hd image records.".format(len(self.imginfo)))

    def _find_msg_by_type(self, msgs=None):
        ret = []
        if msgs is None:
            msgs = itertools.chain.from_iterable(self.msgs_by_chat.itervalues())
        for msg in msgs:
            if msg.type == 34:
                ret.append(msg)
        return sorted(ret)

    def _parse_emoji(self):
        # wechat provided emojis
        query = self.cc.execute(
""" SELECT md5, groupid FROM EmojiInfoDesc """)
        for row in query:
            md5, group = row
            self.emoji_groups[md5] = group

        try:
            query = self.cc.execute(
    """ SELECT md5, catalog, name, cdnUrl, encrypturl, aeskey FROM EmojiInfo""")
        except: # old database does not have cdnurl
            pass
        else:
            for row in query:
                md5, catalog, name, cdnUrl, encrypturl, aeskey = row
                if cdnUrl or encrypturl:
                    self.emoji_info[md5] = (catalog, cdnUrl, encrypturl, aeskey)

    def _parse_img_flag(self):
        """Parse the img_flag table which stores avatar for each id."""
        query = self.cc.execute(
""" SELECT username, reserved1 FROM img_flag """)
        for row in query:
            username, url = row
            if url:
                self.avatar_urls[username] = url

    def _parse(self):
        self._parse_contact()
        self._parse_userinfo()  # depend on self.contacts
        self._parse_msg()
        self._parse_imginfo()
        self._parse_emoji()
        self._parse_img_flag()

    def get_emoji_encryption_key(self):
        # obtain local encryption key in a special entry in the database
        # this also equals to md5(imei)
        query = self.cc.execute("SELECT md5 FROM EmojiInfo where catalog == 153")
        results = list(query)
        if len(results):
            assert len(results) == 1, "Found > 1 encryption keys in EmojiInfo. This is a bug!"
            return results[0][0]
        return None

    # process the values in a row
    def _parse_msg_row(self, row):
        """Parse a record of message into my format.

        Note that message are read in binary format.
        """
        values = dict(zip(WeChatDBParser.FIELDS, row))
        values['createTime'] = datetime.fromtimestamp(values['createTime']/ 1000)
        if values['content']:
            try:
                values['content'] = values['content'].decode()
            except:
                logger.warning(f"Invalid byte sequence in message content (type={values['type']}, createTime={values['createTime']})")
                values['content'] = 'FAILED TO DECODE'
        else:
            values['content'] = ''

        values['talker'] = values['talker'].decode()
        if values['imgPath']:
            values['imgPath'] = values['imgPath'].decode()
        values['chat'] = values['talker']
        try:
            if values['chat'].endswith('@chatroom'):
                values['chat_nickname'] = self.contacts[values['chat']]
                content = values['content']

                if values['isSend'] == 1:
                    values['talker'] = self.username
                elif values['type'] == TYPE_SYSTEM:
                    values['talker'] = 'SYSTEM'
                else:
                    talker = content[:content.find(':')]
                    values['talker'] = talker
                    values['talker_nickname'] = self.contacts.get(talker, talker)

                values['content'] = content[content.find('\n') + 1:]
            else:
                tk_id = values['talker']
                values['chat'] = tk_id
                values['chat_nickname'] = self.contacts[tk_id]
                values['talker'] = tk_id
                values['talker_nickname'] = self.contacts[tk_id]
        except KeyError:
            # It's possible that messages are kept in database after contacts been deleted
            logger.warn("Unknown contact: {}".format(values.get('talker', '')))
            return None
        return values

    @property
    def all_chat_ids(self):
        return self.msgs_by_chat.keys()

    @property
    def all_chat_nicknames(self):
        return [self.contacts[k] for k in self.all_chat_ids if len(self.contacts[k])]

    def get_id_by_nickname(self, nickname):
        """
        Get chat id by nickname.
        """
        l = self.contacts_rev[nickname]
        if len(l) == 0:
            raise KeyError("No contacts have nickname {}".format(nickname))
        if len(l) > 1:
            logger.warn("More than one contacts have nickname {}! Using the first contact".format(nickname))
        return l[0]

    def get_chat_id(self, nick_name_or_id):
        """
        Get the unique chat id by either chat id itself, or the nickname of the chat.
        """
        if nick_name_or_id in self.contacts:
            return nick_name_or_id
        else:
            return self.get_id_by_nickname(nick_name_or_id)

