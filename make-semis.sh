#!/bin/bash

prog=test_dijk
# prog=build_ch
prog=test_hashmap

hosts=""
# hosts="-HHOSTS"

# city="BJ"
fn_cin="./Programs/Public-Input/graph/compile.in"
exec 6< $fn_cin
read NP <&6
read city <&6
# NP=$(head -n 1 $fn_cin)
# NP=4

other=''
# Mod prime / GF2^128
opt=F
# ptcs=(semi hemi temi soho) # Dishonest-Majority
ptcs=(hemi)
# ptcs=(hemi temi)
## ptcs=(atlas shamir)

# Mod 2^k
# opt=R
# ptcs=(semi2k)

# Bin
# opt=B
# ptcs=(semi-bin) # Dishonest-Majority
## ptcs=(ccd)

# other="-G"
# opt=B
# ptcs=(semi-bmr)
## ptcs=(shamir-bmr)

mix=''
mix=-X # daBits
# mix=-Y # EdaBits

bits=64
compile_opts="$other $mix -$opt $bits"
# ./compile.py $compile_opts $prog

opts=''
# opts='-v'
# opts="--bucket-size 10"
fin=''
# fin="-IF Player-Data/Dijk/CAL/graph"
run_opts="$fin $opts -N $NP"
for ptc in ${ptcs[@]}
do
	obj=$ptc-party.x
	# echo $obj
	# make -j8 $obj
	exec="Scripts/$ptc.sh $prog"
	exec="Scripts/compile-run.py $hosts -E $ptc $prog $compile_opts --"

	$exec $run_opts #> $ptc.out
done