#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: timer.py
# Date: Wed Jun 17 23:25:54 2015 +0800
# Author: Yuxin Wu

import time, functools
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

class TotalTimer(object):
    def __init__(self):
        self.times = defaultdict(float)

    def add(self, name, t):
        self.times[name] += t

    def reset(self):
        self.times = defaultdict(float)

    def __del__(self):
        for k, v in self.times.iteritems():
            logger.info("{} took {} seconds in total.".format(k, v))

_total_timer = TotalTimer()
class timing(object):
    def __init__(self, total=False):
        self.total = total

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            ret = func(*args, **kwargs)
            duration = time.time() - start_time

            if hasattr(func, '__name__'):
                func_name = func.__name__
            else:
                func_name = 'function in module {}'.format(func.__module__)
            if self.total:
                _total_timer.add(func_name, duration)
            else:
                logger.info('Duration for `{}\': {}'.format(
                    func_name, duration))
            return ret
        return wrapper

