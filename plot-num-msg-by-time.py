#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: plot_num_msg_by_time.py
# Date: Wed Mar 25 17:44:39 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

from wechat.parser import WeChatDBParser
from wechat.utils import ensure_unicode

from datetime import timedelta, datetime
import numpy as np
import matplotlib.pyplot as plt
import sys, os

if len(sys.argv) != 3:
    sys.exit("Usage: {0} <path to decrypted_database.db> <name>".format(sys.argv[0]))

db_file = sys.argv[1]
name = ensure_unicode(sys.argv[2])
every_k_days = 2

parser = WeChatDBParser(db_file)
msgs = parser.msgs_by_talker[name]
times = [x.createTime for x in msgs]
start_time = times[0]
diffs = [(x - start_time).days for x in times]
max_day = diffs[-1]

width = 20
numbers = range((max_day / width + 1) * width + 1)[::width]
labels = [(start_time + timedelta(x)).strftime("%m/%d") for x in numbers]
plt.xticks(numbers, labels)
plt.xlabel("Date")
plt.ylabel("Number of msgs in k days")
plt.hist(diffs, bins=max_day / every_k_days)
plt.show()

# statistics by hour
# I'm in a different time zone in this period:
#TZ_DELTA = {(datetime(2014, 7, 13), datetime(2014, 10, 1)): -15}
#def real_hour(x):
    #for k, v in TZ_DELTA.iteritems():
        #if x > k[0] and x < k[1]:
            #print x
            #return (x.hour + v + 24) % 24
    #return x.hour
#hours = [real_hour(x) for x in times]
#plt.ylabel("Number of msgs")
#plt.xlabel("Hour in a day")
#plt.hist(hours, bins=24)
#plt.show()
