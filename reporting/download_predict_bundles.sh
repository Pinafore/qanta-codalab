#!/usr/bin/env bash

IFS=$'\n'
uuids="$(cl search worksheet=0xbb0acb9df0cb45b4a8dfcfdcda264ebe name='%-predict' .limit=100 -u)"
for uuid in $uuids
do
	echo $uuid
	cl download $uuid
done;