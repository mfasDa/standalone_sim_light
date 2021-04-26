#! /bin/bash

ENGINE=$1
RUNCARD=$2
NEVENTS=$3
SEED=$4
MACRO=$5

SCRIPTNAME=`readlink -f $0`
REPO=`dirname $SCRIPTNAME`

cmd="$REPO/runtask.py -g $ENGINE -c $RUNCARD -e $NEVENTS -s $SEED"
if [ "x$MACRO" != "x" ]; then
    cmd=$(printf "%s %s" "$cmd" "$MACRO")
fi
eval $cmd