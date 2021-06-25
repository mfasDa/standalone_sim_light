#! /bin/bash

basedir=${1:-$PWD}

bindirs=($(ls -1 $basedir | grep bin))
for bdir in ${bindirs[@]}; do
	cd $bdir
	chunks=$(ls | grep [[:digit:]])
	for chunk in ${chunks[@]}; do
		rm -rf $chunk
	done
	rm -rf logs *.log
	cd $basedir
done