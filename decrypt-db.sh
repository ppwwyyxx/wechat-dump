#!/bin/bash -e
# File: decrypt_db.sh
# Date: Tue Jun 16 22:23:13 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

source compatibility.sh

MSGDB=$1
imei=$2
uin=$3
output=decrypted.db

if [[ -z "$1" || -z "$2" || -z "$3" ]]; then
	echo "Usage: $0 <path to EnMicroMsg.db> <imei> <uin>"
	exit 1
fi

if [[ -f $output ]]; then
	echo -n "$output already exists. removed? (y/n)"
	read r
	[[ $r == "y" ]] && rm -v $output || exit 1
fi


KEY=$(echo -n "$imei$uin" | $MD5SUM | cut -b 1-7)
echo "KEY: $KEY"

uname | grep Darwin > /dev/null && os=darwin || os=linux
uname -m | grep x86_64 > /dev/null && version=64bit || version=32bit
echo "Use $version sqlcipher of $os."

echo "Dump decrypted database... "
echo "Don't worry about libcrypt.so version warning."


SQLCIPHER=./third-party/sqlcipher/$os/$version
export LD_LIBRARY_PATH=$SQLCIPHER
"$SQLCIPHER"/sqlcipher "$MSGDB" << EOF
PRAGMA key='$KEY';
PRAGMA cipher_use_hmac = off;
ATTACH DATABASE "$output" AS db KEY "";
SELECT sqlcipher_export("db");
DETACH DATABASE db;
EOF

echo "Database successfully dumped to $output"
