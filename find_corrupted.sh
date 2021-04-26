#! /bin/bash
INPUTDIR=${1:-`pwd`}

allfiles=($(find $INPUTDIR))
for fl in ${allfiles[@]}; do
    result=$(echo $fl | grep "cannot access")
    if [ "x$(echo result)" != "x" ]; then
        echo $fl
    fi
done