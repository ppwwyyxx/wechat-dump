#!/bin/bash -e
# File: count-message.sh
# Date: Wed Nov 29 02:32:40 2017 -0800
# Author: Kangjing Huang <huangkangjing@gmail.com>


if [[ -z $1 ]]
then
    echo "Usage: $0 [Directory of text messages]"
    exit 1
fi
# TODO work on db directly

echo -e "Filename\t#Lines\t#Chars\t#Words"

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

for i in "$1"/*.txt
do
    echo -en "$i\t"
    LINECOUNT=$(cat "$i"| wc -l )
    CHARCOUNT=$(cat "$i"| sed 's/.*:[0-9][0-9]:\(.*\)/\1/g'  | sed 's/\[.*\]//g'  | grep  -v img | wc -m)
    WORDCOUNT=$(cat "$i"| sed 's/.*:[0-9][0-9]:\(.*\)/\1/g'  | sed 's/\[.*\]//g'  | grep  -v img | wc -w)
    echo -e "$LINECOUNT\t$CHARCOUNT\t$WORDCOUNT"
done | sort -t $'\t' -k 2 -n | column -t -s $'\t'

IFS=$SAVEIFS
