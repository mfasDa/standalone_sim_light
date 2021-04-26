#! /bin/bash
TARGETDIR=$1
echo "Using target directory $TARGETDIR"
BASE=`pwd`
echo "Using base dir $BASE"
files=($(ls -1))
for fl in ${files[@]}; do
    res=$(ls -l 2>&1 | grep $fl | grep -v Permission)
    testfile=$BASE/$fl
    if [ "x$(echo $res | grep "?????????")" == "x" ]; then
        if [ ! -f $fl ]; then continue; fi
        cmd=$(printf "echo %s | sed -e \'s|%s|%s|g\'" $testfile $BASE $TARGETDIR)
        outfile=$(eval $cmd)
        echo "Moving good file to safe location: $outfile"  
        outputdir=`dirname $outfile`
        if [ ! -d $outputdir ]; then mkdir -p $outputdir; fi
        mv $testfile $outfile
    else
        echo Found bad file: $res
    fi
done