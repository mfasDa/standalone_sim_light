#! /bin/bash

SCRIPT=`readlink -f $0`
SOURCE=`dirname $SCRIPT`

base=`pwd`
script=$SOURCE/makeScaled.C
for i in `seq 0 20`; do
	bindir=$(printf "bin%d" $i)
	cd $bindir
	root -l -b -q $script
	cd $base
done
