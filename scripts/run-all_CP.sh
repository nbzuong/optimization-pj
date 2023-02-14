#!/bin/bash
# please run this from root of source code:
#
# ~/optimization$ scripts/run-all_CPM.sh

# change dir to root of project
cd $PWD

outdir=scripts/output/out_CP
analyzedir=scripts/output/analyze_CP

# create output folder
mkdir -p $outdir
mkdir -p $analyzedir

# find all states and store in an array
x=$(cd files/generated_data; find . -name "*.txt" | awk '{print substr($0, 3)}' | sort )

for i in $x; do
	# sanity check
	echo "ping: $i";
	
	# in order: file for algo output, output parser, input for algo
	file="$outdir/out_CP_$i";
	analyze="$analyzedir/analyze_CP_$i";
	filepath="files/generated_data/$i"
	
	# create file for algo output and output parser
	touch $file;
	touch $analyze;
	
	# execute CP & time it
	/usr/bin/time -f "time: %e" -ao $file python3 files/CP_model.py $filepath > $file;

done
	
# run parser
bash scripts/parse-output.sh CP
