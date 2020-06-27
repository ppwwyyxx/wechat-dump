#!/bin/bash -e
# File: decrypt-db.sh
# Date: Tue Jun 16 22:23:13 2015 +0800

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

echo "Dump decrypted database... "

# https://github.com/sqlcipher/sqlcipher/commit/e4b66d6cc8a2b7547a32ff2c3ac52f148eba3516
sqlcipher "$MSGDB" << EOF
PRAGMA key='$KEY';
PRAGMA cipher_compatibility = 1;
ATTACH DATABASE "$output" AS db KEY "";
SELECT sqlcipher_export("db");
DETACH DATABASE db;
EOF

echo "Database successfully dumped to $output"
