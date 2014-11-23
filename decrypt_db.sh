#!/bin/bash -e
# File: decrypt_db.sh
# Date: Sun Nov 23 16:46:51 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

MMSGDB=$1
imei=$2
uin=$3

if [[ -z "$1" || -z "$2" || -z "$3" ]]; then
	echo "Usage: $0 <path to EnMicroMsg.db> <imei> <uin>"
	exit
fi

KEY=$(echo -n "$imei$uin" | md5sum | cut -b 1-7)

LD_LIBRARY_PATH=./lib ./lib/sqlcipher $MMSGDB << EOF
PRAGMA key='$KEY';
PRAGMA cipher_use_hmac = off;
ATTACH DATABASE "decrypted_database.db" AS decrypted_database KEY "";
SELECT sqlcipher_export("decrypted_db");
DETACH DATABASE decrypted_database;
EOF
