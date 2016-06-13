#!/bin/bash
#
# Fixup metadata in OGG files.
#
# Expected directory structure:
#  artist 01/
#    disc 01/
#      disc_01_track_01.ogg
#      disc_01_track_02.ogg
#    disc 02/
#      disc_02_track_01.ogg
#      disc_02_track_02.ogg
#  artist 02/

function usage() {
	echo "USAGE: $(basename $0) <start_dir>"
	echo
	echo "start_dir: artist name"
	echo
}

if [ $# != 1 ]; then
	usage
	exit 1
fi

START_DIR=$1
shift

if [[ "$START_DIR" =~ "/" ]]; then
	echo "Starting directory should not have directory separator"
	exit 1
fi

disc=1
file_num=1
cd "$START_DIR"
for d in *; do
	cd "$d"
	track=1
	for t in *; do
		vorbiscomment -w -t "TRACKNUMBER=$track" -t "DISCNUMBER=$disc" -t "TITLE=$START_DIR $((file_num++))" -t "ARTIST=$START_DIR" "$t"
		track=$((track + 1))
	done
	disc=$((disc + 1))
	cd ..
done
cd ..

echo $file_num " files modified"
