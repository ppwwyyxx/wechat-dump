#!/bin/bash -e

cd `dirname "$0"`/silk
make
make decoder

