#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

FMT = '{}[%(asctime)s %(lineno)d@%(filename)s:%(name)s]\033[0m %(message)s'

class LogLevelFilter(object):
    def __init__(self, level):
        self._level = level
    def filter(self, logRecord):
        return logRecord.levelno <= self._level

def set_level_color(lvl, color):
    handler = logging.StreamHandler()
    handler.setLevel(lvl)
    handler.addFilter(LogLevelFilter(lvl))
    handler.setFormatter(logging.Formatter(FMT.format(color), '%H:%M:%S'))
    logger.addHandler(handler)

set_level_color(logging.INFO, '\033[1;32m')
set_level_color(logging.WARN, '\033[1;33m')
set_level_color(logging.ERROR, '\033[1;31m')

if __name__ == '__main__':
    logger.info("info")
    logger.warning("warn")

