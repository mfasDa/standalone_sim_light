#! /bin/bash
# Pi/K0 stable vs. decayed

MODE=$1

BASE=/home/mfasel_alice/fastsim/HERWIG/HERWIG_standalone_cades
SUBMITTER=$BASE/submit_pythia_many.py
OUTPUTBASE=/lustre/or-scratch/cades-birthright/mfasel_alice/fastsim/PYTHIA/K0Pi0_Acceptance

MACRO=
SIMDIR=
case $MODE in
	1) MACRO=simPythiaK0Pi0Decayed.C
	   SIMDIR=K0DecayedPi0Decayed
	   ;;
	2) MACRO=simPythiaK0DecayedPi0Stable.C
	   SIMDIR=K0DecayedPi0Stable
	   ;;
	3) MACRO=simPythiaK0StablePi0Decayed.C
	   SIMDIR=K0StablePi0Decayed
	   ;;
	4) MACRO=simPythiaK0Pi0Stable.C
	   SIMDIR=K0StablePi0Stable
	   ;;
	*) echo "Mode unsupported"
	   exit 1
	   ;;
esac
OUTPUTDIR=$OUTPUTBASE/$SIMDIR

NJOB=100
NEVENT=100000
EBEAM=6500
ROOTFILE=AnalysisResults.root
PARTITION=high_mem_cd
TIMELIMIT=04:00:00

cmd=$(printf "%s -o %s -j %d -n %d -e %d -r %s -q %s -m %s -t %s" $SUBMITTER $OUTPUTDIR $NJOB $NEVENT $EBEAM $ROOTFILE $PARTITION $MACRO $TIMELIMIT)
eval $cmd