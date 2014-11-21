#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: plot_num_msg_by_time.py
# Date: Fri Nov 21 15:19:00 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

from lib.Parser import WeChatDBParser
from lib.utils import ensure_unicode

from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import sys, os

if len(sys.argv) != 3:
    sys.exit("Usage: {0} <path to decrypted_database.db> <name>".format(sys.argv[0]))

every_k_days = 2
db_file = sys.argv[1]
name = ensure_unicode(sys.argv[2])

parser = WeChatDBParser(db_file)
parser.parse()
msgs = parser.msgs_by_talker[name]
times = [x.createTime for x in msgs]
start_time = times[0]
diffs = [(x - start_time).days for x in times]
max_day = diffs[-1]

width = 30
numbers = range((max_day / width + 1) * width + 1)[::width]
labels = [(start_time + timedelta(x)).strftime("%m/%d") for x in numbers]
plt.xticks(numbers, labels)
plt.xlabel("Date")
plt.ylabel("Number of msgs in k days")
plt.hist(diffs, bins=max_day / every_k_days)
plt.show()
