#!/bin/bash
#Helper script. Splits a *.csv file into two by line
#at random, according to a passed proportion N. 
#N percent ends up in TRAIN, (1-N) in VALID.

htxt="$(basename "$0") [-h] [-s n] -- helper script. Splits a *.csv file into two, 
by line at random, according to a passed proportion N. N percent of the 
original file's lines ends up in --train (at random), (1-N) ends up in --valid.

Automatically uncompressing the file turned out to be surprisingly difficult; manually
uncompress with gunzip -c (file) | (command)  -i -.

Help:
    -h, --help      show this help text

All inputs are required.
	-i              input file (uncompressed)
    -n              splitting proportion (out of 100, should be an integer between 0 and 100)
    -t, --train     training outfile name before *.gz; will be cleared before writing.
    -v, --valid     validation outfile before *.gz; will be cleared before writing."

#parse parameters
while [[ $# > 1 ]]
do
key="$1"

case $key in
	"-h"|"--help")	#Help text
		echo "$htxt"
		exit
	;;
	"-i")			#infile
		INPUT="$2"
		shift 2		#consume option
	;;	
	"-n") 			#Proportion
		N="$2" 	
		shift 2		#consume option
	;;
	"-t"|"--train") #Training outfile
		TRAIN="$2"	
		shift 2		#consume option
	;;
	"-v"|"--valid")	#Validation outfile
		VALID="$2"	
		shift 2		#consume option
	;;
	*)				#unknown option
		echo "Invalid option '$key'." 
		exit
	;;
esac
done

if ! [[ $N && $TRAIN && $VALID && $INPUT ]]; then 
	echo "Missing required option." 
	exit
fi

# Passes all relevant parameters to awk with -v, then gets a random number for every line; 
#if that random number is less than N, send the line to train, otherwise, valid.
#Send the first line (column names) to both files
awk -v prop=$N -v train="$TRAIN" -v valid="$VALID" '
BEGIN {srand()} 
!/^$/ {
	if ( FNR == 1) {
		print $0 >> train;
		print $0 >> valid;
	}
	else if (rand() <= prop) 
		print $0 >> train; 
	else	
		print $0 >> valid;}' $INPUT

#Compresses files
gzip -f "$TRAIN"
gzip -f "$VALID"

echo "Done."