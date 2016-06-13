#!/bin/bash

set -o errexit

function usage()
{
	echo "$(basename $0) <device> <name_for_device_mapper>"
	echo "Open a Truecrypt volume using Device Mapper."
	echo
}

#check command line parameter count
[ $# != 2 ] && { usage; exit 1; }

dev=$1
shift
name=$1
shift

#check if we are root so we can run cryptsetup
[ $(id -u) -ne 0 ] && { echo "Must be root!"; exit 1; }

#check if device exists
[ ! -e "$dev" ] && { echo "Cannot find device!"; exit 1; }

zenity --password --text="Enter passphrase: " | cryptsetup open --type tcrypt "$dev" "$name"

