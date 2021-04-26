#! /bin/bash
TARGET=$1
BASE=$PWD
SCRIPTNAME=`readlink -f $0`
SOURCEDIR=`dirname $SCRIPTNAME`
MOVESCRIPT_DATA=$SOURCEDIR/scanAnalysisResults.sh
MOVESCRIPT_LOGS=$SOURCEDIR/saveGoodFilesInDirectory.sh
dirs=($(ls -1))
fls=("herwig" "log" "in" "AnalysisResults.root" "events.hepmc")
for dr in ${dirs[@]}; do
    cd $dr
    TARGETDIR=$TARGET/$dr
    INPUTDIR=$BASE/$dr
    for fl in ${fls[@]}; do
        cmd=$(printf "%s %s %s" $MOVESCRIPT_DATA $TARGETDIR $fl)
        eval $cmd
    done

    globfiles=("AnalysisResults.root" "herwig.in" "merge.log")
    for gf in ${globfiles[@]}; do
        testfile=$INPUTDIR/$gf
        res=$(ls -l 2>&1 | grep $gf | grep -v Permission)
        if [ "x$(echo $res | grep "?????????")" == "x" ]; then
            if [ -f $testfile ]; then
                cmd=$(printf "echo %s | sed -e \'s|%s|%s|g\'" $testfile $INPUTDIR $TARGETDIR)
                outfile=$(eval $cmd)
                echo "Moving good file to safe location: $outfile"  
                outputdir=`dirname $outfile`
            fi
        if [ ! -d $outputdir ]; then mkdir -p $outputdir; fi
            mv $testfile $outfile
        else
            echo Found bad file: $res
        fi
    done

    cd $PWD/logs
    LOGDIR=$TARGETDIR/logs
    cmd=$(printf "%s %s" $MOVESCRIPT_LOGS $LOGDIR)
    eval $cmd

    cd $BASE
done