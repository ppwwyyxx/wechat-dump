#!/bin/bash -e
# File: compile_silk.sh
# Date: Tue Jun 16 22:26:49 2015 +0800
# Author: Yuxin Wu

cd `dirname "$0"`/silk
make
make decoder

