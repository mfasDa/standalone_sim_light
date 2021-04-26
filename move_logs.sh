#! /bin/bash
TARGET=$1
BASE=$PWD
MOVESCRIPT=/home/mfasel_alice/fastsim/HERWIG/HERWIG_standalone_cades/saveGoodFilesInDirectory.sh
for binID in `seq 12 20`; do
    echo "Doing bin $binID"
    bindir=$(printf "bin%d/logs" $binID)
    indir=$BASE/$bindir
    outdir=$TARGET/$bindir
    cd $indir
    cmd=$(printf "%s %s" $MOVESCRIPT $outdir)
    echo $cmd
    eval $cmd
done
cd $BASE