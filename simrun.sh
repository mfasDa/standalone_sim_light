#! /bin/bash

CLUSTER=$1
ENGINE=$2
RUNCARD=$3
NEVENTS=$4
SEED=$5
MACRO=$6

CLUSTER_HOME=
if [ $CLUSTER == "CADES" ]; then
    CLUSTER_HOME=$HOME
elif [ $CLUSTER == "B587" ]; then
    CLUSTER_HOME=/software/markus/alice
fi
# Additional PDF sets locally installed
source $CLUSTER_HOME/lhapdf_data_setenv

SCRIPTNAME=`readlink -f $0`
REPO=`dirname $SCRIPTNAME`

cmd="$REPO/runtask.py -g $ENGINE -c $RUNCARD -e $NEVENTS -s $SEED"
if [ "x$MACRO" != "x" ]; then
    cmd=$(printf "%s %s" "$cmd" "$MACRO")
fi
eval $cmd