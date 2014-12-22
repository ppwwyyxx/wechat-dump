#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: msgslice.py
# Date: Mon Dec 22 23:07:02 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

class MessageSlicer(object):
    """ Separate messages into slices by time.
        A new day always begins a new slice.
    """
    def __init__(self, diff_thres=5 * 60):
        self.diff_thres = diff_thres

    def slice(self, msgs):
        ret = []
        now = []
        for m in msgs:
            if len(now) == 0:
                now.append(m)
                continue
            nowtime, lasttime = m.createTime, now[-1].createTime
            if nowtime.date() == lasttime.date() and \
               (nowtime - lasttime).seconds < self.diff_thres:
                now.append(m)
                continue

            ret.append(now)
            now = [m]
        ret.append(now)

        assert len(msgs) == sum([len(k) for k in ret])
        return ret


