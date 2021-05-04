#! /bin/bash

INPUTLIST=$1
OUTPUTDIR=$2
MACRO=$3

echo "Running analysis on existing sample ..."

if [ ! -f $INPUTLIST ]; then
    echo "List with inputfiles $INPUTLIST not found, exiting ..."
    exit 1
fi

#source $HOME/alice_setenv
PACKAGES=(ROOT fastjet HepMC)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`

if [ ! -d $OUTPUTDIR ]; then mkdir -p $OUTPUTDIR; fi
cd $OUTPUTDIR

# Analysing current file
FILEINDEX=0
ROOTFILE=
FILEBASE=
while read filename; do
    echo "Processing file $filename"
    cmd=$(printf "root -l -b -q \'%s(\"%s\")\' &> analysis.log" $MACRO $filename)
    eval $cmd
    if [ "x$ROOTFILE" == "x" ]; then 
        ROOTFILE=$(ls -1 | grep root)
        FILEBASE=$(echo $ROOTFILE | cut -d '.' -f 1)
    fi
    TMPFILE=$(printf "%s_%d.root" $FILEBASE $FILEINDEX)
    mv $ROOTFILE $TMPFILE
    let "FILEINDEX++"
done < $INPUTLIST

# Merge results
PATTERN=$(printf "%s_" $FILEBASE)
ALLFILES=($(ls -1))
DELFILES=()
MERGECMD=$(printf "hadd -f %s" $ROOTFILE)
for tstfile in ${ALLFILES[@]}; do
    if [ "x$(echo $tstfile | grep $FILEBASE)" != "x" ]; then
        MERGECMD=$(printf "%s %s" "$MERGECMD" $tstfile)
        DELFILES+=($tstfile)
    fi
done
eval $MERGECMD

# Delete temporary files
for delfile in ${DELFILES[@]}; do
    rm -v $delfile
done