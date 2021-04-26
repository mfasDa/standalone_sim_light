#! /bin/bash
NEVENTS=$1
SEED=$2
MACRO=$3

source $HOME/alice_setenv
PACKAGES=(Herwig ROOT)
ALIENV=`which alienv`
for pack in ${PACKAGES[@]}; do
    eval `$ALIENV --no-refresh load $pack/latest` 
done
eval `$ALIENV list`
# Additional PDF sets locally installed
source $HOME/lhapdf_data_setenv

echo "Using random seed                 $SEED"
echo "Simulating number of events       $NEVENTS"
Herwig --repo=$HERWIG_ROOT/share/Herwig/HerwigDefaults.rpo read herwig.in &> hw_setup.log
Herwig --repo=$HERWIG_ROOT/share/Herwig/HerwigDefaults.rpo run herwig.run -N $NEVENTS -s $SEED &> hw_run.log

cmd=$(printf "root -l -b -q \'%s(\"events.hepmc\")\' &> analysis.log" $MACRO)
eval $cmd
