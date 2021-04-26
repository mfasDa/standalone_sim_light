#! /bin/bash
NEVENTS=$1
SEED=$2
ENERGYCMS=$3
PTHARDBIN=$4
MACRO=$5

source $HOME/alice_setenv
PACKAGES=(pythia ROOT fastjet)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`
# Additional PDF sets locally installed
source $HOME/lhapdf_data_setenv

echo "Using random seed                 $SEED"
echo "CMS energy                        $ENERGYCMS"
echo "Pt-hard bin                       $PTHARDBIN"
echo "Simulating number of events       $NEVENTS"

cmd=$(printf "root -l -b -q \'%s(%d, %d, %d, %d)\' &> analysis.log" $MACRO $PTHARDBIN $SEED $ENERGYCMS $NEVENTS)
eval $cmd
