#!/bin/bash -e
# File: decrypt_db.sh
# Date: Wed Dec 31 23:38:16 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

MSGDB=$1
imei=$2
uin=$3
output=decrypted.db

if [[ -z "$1" || -z "$2" || -z "$3" ]]; then
	echo "Usage: $0 <path to EnMicroMsg.db> <imei> <uin>"
	exit
fi

KEY=$(echo -n "$imei$uin" | md5sum | cut -b 1-7)
echo "KEY: $KEY"

uname -m | grep x86_64 > /dev/null || version=32bit && version=64bit
echo "Use $version sqlcipher."

echo "Dump decrypted database... "
echo "Don't worry about libcrypt.so version warning."


SQLCIPHER=./sqlcipher/$version
export LD_LIBRARY_PATH=$SQLCIPHER
$SQLCIPHER/sqlcipher $MSGDB << EOF
PRAGMA key='$KEY';
PRAGMA cipher_use_hmac = off;
ATTACH DATABASE "$output" AS db KEY "";
SELECT sqlcipher_export("db");
DETACH DATABASE db;
EOF

echo "Database successfully dumped to $output"
