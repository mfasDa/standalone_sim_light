#! /bin/bash
CLUSTER=$1
NEVENTS=$2
SEED=$3
ENERGYCMS=$4
PTHARDBIN=$5
MACRO=$6

CLUSTER_HOME=
if [ $CLUSTER == "CADES" ]; then
    CLUSTER_HOME=$HOME
elif [ $CLUSTER == "B587" ]; then
    CLUSTER_HOME=/software/markus/alice
fi

envscript=$CLUSTER_HOME/alice_setenv
if [ -f $envscript ]; then
    source $CLUSTER_HOME/alice_setenv
fi
PACKAGES=(pythia ROOT fastjet)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`
# Additional PDF sets locally installed
source $CLUSTER_HOME/lhapdf_data_setenv

echo "Using random seed                 $SEED"
echo "CMS energy                        $ENERGYCMS"
echo "Pt-hard bin                       $PTHARDBIN"
echo "Simulating number of events       $NEVENTS"

cmd=$(printf "root -l -b -q \'%s(%d, %d, %d, %d)\' &> analysis.log" $MACRO $PTHARDBIN $SEED $ENERGYCMS $NEVENTS)
eval $cmd
