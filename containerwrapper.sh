#! /bin/bash

source $HOME/alice_setenv
cmd=""
first=1
for argID in "$@"; do
    if [ $first -eq 0 ]; then
        cmd=$(printf "%s %s" "$cmd" "$argID")
    else
        cmd="$argID"
        first=0
    fi
done
echo "Container wrapper: Launching $cmd"
eval $cmd