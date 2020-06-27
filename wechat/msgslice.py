# -*- coding: UTF-8 -*-

class MessageSlicerByTime(object):
    """ Separate messages into slices by time,
        for time display in html.
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

class MessageSlicerBySize(object):
    """ Separate messages into slices by max slice size,
        to avoid too large html.
    """
    def __init__(self, size=1000):
        """ a slice will have <= 1.5 * cnt messages"""
        self.size = size
        assert self.size > 1

    def slice(self, msgs):
        ret = []
        now = []
        for m in msgs:
            if len(now) >= self.size:
                nowtime, lasttime = m.createTime, now[-1].createTime
                if nowtime.date() != lasttime.date():
                    ret.append(now)
                    now = [m]
                    continue
            now.append(m)
        if len(now) > self.size / 2 or len(ret) == 0:
            ret.append(now)
        else:
            ret[-1].extend(now)
        assert len(msgs) == sum([len(k) for k in ret])
        return ret
