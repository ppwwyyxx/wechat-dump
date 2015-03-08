#!/bin/bash -e
# File: android-interact.sh
# Date: Sat Mar  7 20:57:51 2015 +0800
# Author: Kangjing Huang <huangkangjing@gmail.com>


if [[ -z $1 ]]
then 
    echo "Usage: $0 [Directory of text messages]"
    exit 1
fi

echo -e "Filename\tCounts of message\tCounts of chars\tCounts of words" 

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

for i in "$1"/*.txt
do
    echo -en "$i\t"
    LINECOUNT=$(cat "$i"| wc -l )
    CHARCOUNT=$(cat "$i"| sed 's/.*:[0-9][0-9]:\(.*\)/\1/g'  | sed 's/\[.*\]//g'  | grep  -v img | wc -m)
    WORDCOUNT=$(cat "$i"| sed 's/.*:[0-9][0-9]:\(.*\)/\1/g'  | sed 's/\[.*\]//g'  | grep  -v img | wc -w)
    echo -e "$LINECOUNT\t$CHARCOUNT\t$WORDCOUNT"
done

IFS=$SAVEIFS
