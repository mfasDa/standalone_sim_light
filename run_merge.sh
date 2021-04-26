#! /bin/bash
WORKDIR=$1
ROOTFILE=$2

source $HOME/alice_setenv
PACKAGES=(ROOT)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`

cd $WORKDIR
dirs=($(ls -1))
fls=()
for d in ${dirs[@]}; do
    fname=$d/$ROOTFILE
    if [ -f $fname ]; then
        fls+=($fname)
    fi
done

cmd=$(printf "hadd -f %s" $ROOTFILE)
for f in ${fls[@]}; do
    cmd=$(printf "%s %s" "$cmd" $f)
done
echo "Doing command:"
echo $cmd
eval $cmd