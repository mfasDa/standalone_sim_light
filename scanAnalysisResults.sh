#! /bin/bash
TARGETDIR=$1
echo "Using target directory $TARGETDIR"
FILE=${2:-AnalysisResults.root}
BASE=`pwd`
echo "Using base dir $BASE"
dirs=($(ls -1 $BASE))
for slotdir in ${dirs[@]}; do
  if [ ! -d $BASE/$slotdir ]; then continue; fi
  if [ "x$(echo $slotdir | grep log)" != "x" ]; then continue; fi
  cd $BASE/$slotdir
  echo "Doing slot $slotdir" 
  allfiles=($(ls -1))
  for fl in ${allfiles[@]}; do
    if [ "x$(echo $fl | grep $FILE)" != "x" ]; then
      echo "Using selected file $fl"
      res=$(ls -l 2>&1 | grep $fl | grep -v Permission)
      testfile=$PWD/$fl
      if [ "x$(echo $res | grep "?????????")" == "x" ]; then
        cmd=$(printf "echo %s | sed -e \'s|%s|%s|g\'" $testfile $BASE $TARGETDIR)
        outfile=$(eval $cmd)
        echo "Moving good file to safe location: $outfile"  
        outputdir=`dirname $outfile`
        if [ ! -d $outputdir ]; then mkdir -p $outputdir; fi
        mv $testfile $outfile
      else
        echo Found bad file: $res
      fi
    fi
  done
  cd $BASE
done

