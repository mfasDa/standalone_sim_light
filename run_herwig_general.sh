#! /bin/bash
CLUSTER=$1
NEVENTS=$2
SEED=$3
MACRO=$4

CLUSTER_HOME=
if [ $CLUSTER == "CADES" ]; then
    CLUSTER_HOME=$HOME
elif [ $CLUSTER == "B587" ]; then
    CLUSTER_HOME=/software/markus/alice
fi

PACKAGES=(Herwig ROOT)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`
# Additional PDF sets locally installed
source $CLUSTER_HOME/lhapdf_data_setenv

echo "Using random seed                 $SEED"
echo "Simulating number of events       $NEVENTS"
Herwig --repo=$HERWIG_ROOT/share/Herwig/HerwigDefaults.rpo read herwig.in &> hw_setup.log
Herwig --repo=$HERWIG_ROOT/share/Herwig/HerwigDefaults.rpo run herwig.run -N $NEVENTS -s $SEED &> hw_run.log

cmd=$(printf "root -l -b -q \'%s(\"events.hepmc\")\' &> analysis.log" $MACRO)
eval $cmd
