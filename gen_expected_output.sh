#! /bin/bash

# generate the expected output for the unittests

for f in test/*.ulg; do
	echo "Processing $f"
	ulog_info -v "$f" > "${f%.*}"_info.txt
	ulog_messages "$f" > "${f%.*}"_messages.txt
	#ulog_params "$f" > "${f%.*}"_params.txt
done
