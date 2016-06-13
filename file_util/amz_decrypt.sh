#!/bin/bash
#
# base64 decode an .amz file then decrypt it

set -o errexit

function usage(){
	echo "$(basename $0) <amz_file> <out_file>"
	echo -e "\tout_file: XML file containing a URL to then download the MP3"
	echo
	exit 1
}

if [ $# -ne 2 ]; then usage; fi

amz_file=$1
shift
out_file=$1

tmp_file=`mktemp`
base64 -d "$amz_file" > "$tmp_file"
openssl des-cbc -in "$tmp_file" -out "$out_file" -d -K 29AB9D18B2449E31 -iv 29AB9D18B2449E31
rm "$tmp_file"
